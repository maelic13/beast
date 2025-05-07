import operator
from collections import defaultdict
from multiprocessing import Event, Queue
from random import choice
from threading import Timer
from time import time
from typing import TYPE_CHECKING

from chess import PAWN, QUEEN, Board, Move, Piece, Square

from beast.constants import Constants
from beast.heuristic import (
    ClassicalHeuristic,
    Heuristic,
    HeuristicType,
    LegacyNeuralNetwork,
    NeuralNetwork,
    PieceValues,
    RandomHeuristic,
)

from .search_options import SearchOptions

if TYPE_CHECKING:
    from engine_command import EngineCommand


class Engine:
    def __init__(self, queue: Queue) -> None:
        self._heuristic: Heuristic | None = None
        self._nodes_searched = 0
        self._queue = queue
        self._timeout = Event()
        self._transposition_table: dict[str, tuple[float, int, Move]] = {}
        self._killer_moves: dict[int, list[Move]] = defaultdict(list)
        self._history_table: dict[tuple[Piece, Square], int] = defaultdict(int)

    def start(self) -> None:
        """
        Start the engine process, wait for EngineCommand and search for best move when required.
        """
        while True:
            # check queue for command
            command: EngineCommand = self._queue.get()

            if command.quit:
                break
            if command.stop:
                continue

            # Reset search-related data structures
            self._transposition_table.clear()
            self._killer_moves.clear()
            self._history_table.clear()

            self._heuristic = self._choose_heuristic(command.search_options)
            self._start_timer(command.search_options)
            self._search(command.search_options.board, command.search_options.depth)

    def _check_stop(self) -> None:
        """
        Check if stop conditions were met:
            time for calculation is used up
            stop or quit commands received
        :raise RuntimeError: stop calculation
        """
        if self._timeout.is_set():
            msg = "Time-out."
            raise RuntimeError(msg)

        if self._queue.empty():
            return

        command = self._queue.get_nowait()
        if command.stop or command.quit:
            msg = f"Command: stop - {command.stop}, quit - {command.quit}"
            raise RuntimeError(msg)

    @staticmethod
    def _choose_heuristic(search_options: SearchOptions) -> Heuristic:
        """
        Initialize a heuristic function based on search parameters.
        :param search_options: search parameters
        """
        classical_heuristic = ClassicalHeuristic(
            fifty_moves_rule=search_options.fifty_moves_rule,
            syzygy_path=search_options.syzygy_path,
            syzygy_probe_limit=search_options.syzygy_probe_limit,
        )

        if search_options.heuristic_type == HeuristicType.CLASSICAL:
            return classical_heuristic

        if search_options.heuristic_type == HeuristicType.RANDOM:
            search_options.depth = 1
            return RandomHeuristic()

        if search_options.model_file is None:
            msg = "Warning: incorrect model file."
            raise RuntimeError(msg)

        if search_options.heuristic_type == HeuristicType.NEURAL_NETWORK:
            return NeuralNetwork(
                model_file=search_options.model_file,
                fifty_moves_rule=search_options.fifty_moves_rule,
                syzygy_path=search_options.syzygy_path,
                syzygy_probe_limit=search_options.syzygy_probe_limit,
            )

        if search_options.heuristic_type == HeuristicType.LEGACY_NEURAL_NETWORK:
            return LegacyNeuralNetwork(
                model_file=search_options.model_file,
                fifty_moves_rule=search_options.fifty_moves_rule,
                syzygy_path=search_options.syzygy_path,
                syzygy_probe_limit=search_options.syzygy_probe_limit,
            )

        return classical_heuristic

    def _start_timer(self, search_options: SearchOptions) -> None:
        """
        Check search options and start the timer if there is limited time for the best move search.
        :param search_options: search parameters
        """
        self._timeout.clear()

        if not search_options.has_time_options:
            # do not start the timer
            return

        time_for_move: float | None = None
        if search_options.movetime != 0:
            time_for_move = (search_options.movetime - Constants.TIME_FLEX) / 1000.0
        elif search_options.board.turn and search_options.white_time != 0:
            # Adjust time management based on game stage and remaining time
            moves_left = self._estimate_remaining_moves(search_options.board)
            time_for_move = (search_options.white_time / moves_left - Constants.TIME_FLEX) / 1000.0
        elif not search_options.board.turn and search_options.black_time != 0:
            moves_left = self._estimate_remaining_moves(search_options.board)
            time_for_move = (search_options.black_time / moves_left - Constants.TIME_FLEX) / 1000.0

        if time_for_move is None:
            # wrong time options, do not start timer
            return

        timer = Timer(time_for_move, self._timeout.set)
        timer.start()

    def _estimate_remaining_moves(self, board: Board) -> float:
        """
        Estimate the number of moves remaining in the game based on piece count.
        This helps with time management.
        """
        piece_count = len(board.piece_map())
        if piece_count > 24:  # Opening
            return 40.0
        if piece_count > 10:  # Middlegame
            return 20.0
        # Endgame
        return 15.0

    def _search(self, board: Board, max_depth: float) -> None:
        """
        Search for the best move and report info to stdout using iterative deepening.
        :param board: current board representation
        :param max_depth: limit for depth of iterative search
        """
        # start with a random move choice, to be used in case of timeout before
        # the first depth is reached
        moves: list[Move] = [choice(list(board.legal_moves))]
        depth = 0
        search_started = time() - 0.0001
        self._nodes_searched = 0

        try:
            # Iterative deepening
            for depth in range(1, int(max_depth) + 1):
                evaluation, moves = self._negamax(
                    board, depth, float("-inf"), float("inf"), 0, True
                )

                current_time = time() - search_started
                print(
                    f"info depth {depth} score cp {evaluation} "
                    f"nodes {self._nodes_searched} nps {int(self._nodes_searched / current_time)} "
                    f"time {round(1000 * current_time)} "
                    f"pv {' '.join([move.uci() for move in moves])}",
                    flush=True,
                )

                # Early stop if we're consuming too much time
                if self._timeout.is_set() or (
                    current_time > 0 and self._nodes_searched / current_time < 1000
                ):
                    break
        except RuntimeError:
            # Handle timeout or other interruptions
            pass

        print(f"bestmove {moves[0].uci()}", flush=True)

    def _negamax(
        self,
        board: Board,
        depth: float,
        alpha: float,
        beta: float,
        ply: int,
        is_pv_node: bool = False,
    ) -> tuple[float, list[Move]]:
        """
        Enhanced negamax with move ordering, transposition table, and additional pruning.
        :param board: chess board representation
        :param depth: allowed depth for deepening
        :param alpha: search parameter alpha
        :param beta: search parameter beta
        :param ply: current ply from root
        :param is_pv_node: whether this node is in the principal variation
        :return: evaluation, best move continuation from given position
        """
        self._check_stop()
        self._nodes_searched += 1

        # Check for repetition
        if board.is_repetition(2):
            return 0, []  # Draw

        # Mate distance pruning
        alpha = max(alpha, -30000 + ply)
        beta = min(beta, 30000 - ply - 1)
        if alpha >= beta:
            return alpha, []

        # Transposition table lookup
        board_key = board.fen().split(" ")[0]
        tt_entry = self._transposition_table.get(board_key)
        if tt_entry and tt_entry[1] >= depth:
            tt_score, _, tt_move = tt_entry
            if not is_pv_node:
                return tt_score, [tt_move] if tt_move else []

        is_check = board.is_check()

        # Basic conditions
        if board.is_game_over():
            if board.is_checkmate():
                return -29000 - ply, []  # Prefer shorter mate sequences
            return 0, []  # Draw

        # Extend search in check
        if is_check:
            depth += 0.5

        # Quiescence search at leaf nodes
        if depth <= 0:
            return self._quiescence(board, alpha, beta, ply), []

        # Null move pruning (skip in endgame, check, or at low depths)
        if depth >= 3 and not is_check and not is_pv_node and self._is_null_move_safe(board):
            R = 2 + depth // 6  # Dynamic reduction
            board.push(Move.null())
            null_score, _ = self._negamax(board, depth - 1 - R, -beta, -beta + 1, ply + 1)
            board.pop()
            null_score = -null_score

            if null_score >= beta:
                return beta, []  # Fail-high

        # Initialize best move tracking
        best_score = float("-inf")
        best_moves = []
        tt_move = tt_entry[2] if tt_entry else None

        # Get ordered moves
        ordered_moves = self._order_moves(board, depth, tt_move, ply)
        moves_searched = 0

        # Full-width search
        for move in ordered_moves:
            board.push(move)

            # Late move reductions for non-tactical moves
            if (
                moves_searched >= 3
                and depth >= 3
                and not is_check
                and not board.is_check()
                and not is_pv_node
                and not board.is_capture(move)
            ):
                # Reduced depth for non-promising moves
                R = 1 + (moves_searched // 6) + (depth // 8)
                score, continuation = self._negamax(
                    board, depth - 1 - R, -alpha - 1, -alpha, ply + 1
                )
                score = -score

                # Re-search if the reduced search indicates this might be a good move
                if score > alpha:
                    score, continuation = self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
                    score = -score
            # Normal search for promising or tactical moves
            elif moves_searched == 0 or not is_pv_node:
                score, continuation = self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
                score = -score
            else:
                # PVS search - try to prove this isn't better than our best move
                score, continuation = self._negamax(board, depth - 1, -alpha - 1, -alpha, ply + 1)
                score = -score

                # If the score is within the window and not fail-low, do a full re-search
                if alpha < score < beta:
                    score, continuation = self._negamax(
                        board, depth - 1, -beta, -alpha, ply + 1, True
                    )
                    score = -score

            board.pop()
            moves_searched += 1

            if score > best_score:
                best_score = score
                continuation.insert(0, move)
                best_moves = continuation

                if score > alpha:
                    alpha = score
                    # Update history table for good moves
                    if not board.is_capture(move):
                        piece = board.piece_at(move.from_square)
                        if piece:
                            self._history_table[piece, move.to_square] += depth * depth

            if alpha >= beta:
                # Store killer moves (non-captures that cause beta cutoffs)
                if not board.is_capture(move):
                    if len(self._killer_moves[ply]) < 2:
                        self._killer_moves[ply].append(move)
                    elif move not in self._killer_moves[ply]:
                        self._killer_moves[ply][1] = self._killer_moves[ply][0]
                        self._killer_moves[ply][0] = move
                break

        # Store position in transposition table
        if best_moves:
            self._transposition_table[board_key] = (best_score, depth, best_moves[0])

        return alpha, best_moves

    def _is_null_move_safe(self, board: Board) -> bool:
        """
        Check if it's safe to use null move pruning.
        Avoid in endgames where zugzwang is likely.
        """
        # Don't use null move in endgames with few pieces
        piece_count = len(board.piece_map())
        if piece_count <= 10:
            return False

        # Don't use null move if the side to move has only king and pawns
        has_non_pawn = False
        for piece in board.piece_map().values():
            if piece.piece_type != PAWN and piece.color == board.turn:
                has_non_pawn = True
                break

        return has_non_pawn

    def _order_moves(
        self, board: Board, depth: float, tt_move: Move = None, ply: int = 0
    ) -> list[Move]:
        """
        Order moves to improve alpha-beta pruning efficiency.
        Order: TT move, captures (MVV-LVA), killer moves, history heuristic
        """
        moves = list(board.legal_moves)
        move_scores = []

        for move in moves:
            score = 0

            # 1. Transposition table move
            if tt_move and move == tt_move:
                score = 20000
            # 2. Capturing moves (MVV-LVA)
            elif board.is_capture(move):
                victim_value = self._get_piece_value(board, move.to_square)
                aggressor_value = self._get_piece_value(board, move.from_square)

                if aggressor_value > 0:
                    score = 10000 + (victim_value * 100) - aggressor_value
                else:
                    score = 10000 + victim_value

                # Prioritize promotions
                if move.promotion:
                    score += 8000 + PieceValues.as_dict().get(move.promotion, 0)
            # 3. Check moves
            elif board.gives_check(move):
                score = 9000
            # 4. Killer moves
            elif move in self._killer_moves.get(ply, []):
                killer_index = self._killer_moves[ply].index(move)
                score = 8000 - killer_index * 1000
            # 5. History heuristic
            else:
                piece = board.piece_at(move.from_square)
                if piece:
                    score = self._history_table.get((piece, move.to_square), 0)

            move_scores.append((move, score))

        # Sort moves by score (descending)
        move_scores.sort(key=operator.itemgetter(1), reverse=True)
        return [move for move, _ in move_scores]

    def _get_piece_value(self, board: Board, square: Square) -> int:
        """
        Get the value of a piece on a square.
        Used for MVV-LVA move ordering.
        """
        piece = board.piece_at(square)
        if piece is None:
            # Handle en passant captures
            if board.ep_square == square:
                return PieceValues.as_dict().get(PAWN, 100)
            return 0
        return PieceValues.as_dict().get(piece.piece_type, 0)

    def _quiescence(self, board: Board, alpha: float, beta: float, ply: int = 0) -> float:
        """
        Enhanced quiescence search with move ordering and delta pruning.
        """
        self._check_stop()
        self._nodes_searched += 1

        # Stand-pat evaluation
        stand_pat = self._heuristic.evaluate(board)

        # Beta cutoff
        if stand_pat >= beta:
            return beta

        # Update alpha if stand-pat is better
        alpha = max(alpha, stand_pat)

        # Determine if we can use delta pruning
        is_endgame = len(board.piece_map()) <= 12
        use_delta_pruning = not is_endgame and len(board.piece_map()) > 8

        # Get sorted captures and checks
        captures_and_checks = self._get_sorted_captures_and_checks(board)

        # Search captures and checks
        for move in captures_and_checks:
            # Delta pruning - skip if even capturing queen wouldn't improve alpha
            if use_delta_pruning and board.is_capture(move):
                captured_piece = (
                    PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
                )
                piece_value = PieceValues.as_dict().get(captured_piece, 0)
                potential_gain = piece_value + (900 if move.promotion == QUEEN else 0)

                if stand_pat + potential_gain + 200 < alpha:
                    continue

            board.push(move)
            score = -self._quiescence(board, -beta, -alpha, ply + 1)
            board.pop()

            if score >= beta:
                return beta
            alpha = max(alpha, score)

        return alpha

    def _get_sorted_captures_and_checks(self, board: Board) -> list[Move]:
        """
        Get captures and checks, sorted by MVV-LVA for quiescence search.
        """
        moves = []

        for move in board.legal_moves:
            if board.is_capture(move) or board.gives_check(move):
                # Calculate score for sorting
                score = 0
                if board.is_capture(move):
                    victim_type = (
                        PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
                    )
                    aggressor_type = board.piece_type_at(move.from_square)
                    victim_value = PieceValues.as_dict().get(victim_type, 0)
                    aggressor_value = PieceValues.as_dict().get(aggressor_type, 0)

                    # MVV-LVA: Most Valuable Victim - Least Valuable Aggressor
                    score = victim_value * 100 - aggressor_value

                    # Prioritize promotions
                    if move.promotion:
                        score += 1000

                # Add checks
                if board.gives_check(move):
                    score += 50

                moves.append((move, score))

        # Sort by score (descending)
        moves.sort(key=operator.itemgetter(1), reverse=True)
        return [move for move, _ in moves]
