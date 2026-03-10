import operator
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from multiprocessing import Event, Queue
from random import choice
from threading import Timer
from time import time

from chess import PAWN, Board, Move

from beast_chess.heuristics import (
    ClassicalHeuristic,
    Heuristic,
    HeuristicType,
    NeuralNetwork,
    PieceValues,
    RandomHeuristic,
)
from beast_chess.infra import Constants, EngineCommand, SearchOptions


@dataclass(slots=True)
class TranspositionEntry:
    depth: int
    score: float
    bound: str
    best_move: Move | None


class Engine:
    def __init__(self, queue: Queue) -> None:
        self._heuristic: Heuristic | None = None
        self._nodes_searched = 0
        self._queue = queue
        self._quit_requested = False
        self._search_timer: Timer | None = None
        self._timeout = Event()
        self._tt: dict[tuple[object, ...], TranspositionEntry] = {}

    def start(self) -> None:
        """
        Start the engine process, wait for EngineCommand and search for the best move when required.
        """
        while True:
            if self._quit_requested:
                break

            # check queue for command
            command: EngineCommand = self._queue.get()

            if command.quit:
                break
            if command.stop:
                continue

            self._heuristic = self._choose_heuristic(command.search_options)
            self._start_timer(command.search_options)
            self._search(command.search_options.board, command.search_options.depth)
            if self._quit_requested:
                break

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

        if self._quit_requested:
            msg = "Quit requested."
            raise RuntimeError(msg)

        if self._queue.empty():
            return

        command = self._queue.get_nowait()
        if command.quit:
            self._quit_requested = True
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
                threads=search_options.threads,
            )

        return classical_heuristic

    def _start_timer(self, search_options: SearchOptions) -> None:
        """
        Check search options and start the timer if there is limited time for the best move search.
        :param search_options: search parameters
        """
        self._timeout.clear()
        if self._search_timer is not None:
            self._search_timer.cancel()
            self._search_timer = None

        match (
            search_options.board.turn,
            search_options.move_time,
            search_options.white_time,
            search_options.white_increment,
            search_options.black_time,
            search_options.black_increment,
        ):
            case (_, 0, 0, 0, 0, 0):
                return
            case (_, move_time, _, _, _, _) if move_time > 0:
                time_for_move = move_time
            case (True, _, white_time, 0, _, _) if white_time > 0:
                time_for_move = 0.05 * (white_time - Constants.TIME_FLEX)
            case (True, _, white_time, white_increment, _, _) if white_time > 0:
                time_for_move = min(
                    0.1 * white_time + white_increment - Constants.TIME_FLEX,
                    white_time - Constants.TIME_FLEX,
                )
            case (False, _, _, _, black_time, 0) if black_time > 0:
                time_for_move = 0.05 * (black_time - Constants.TIME_FLEX)
            case (False, _, _, _, black_time, black_increment) if black_time > 0:
                time_for_move = min(
                    0.1 * black_time + black_increment - Constants.TIME_FLEX,
                    black_time - Constants.TIME_FLEX,
                )
            case _:
                msg = "Incorrect time options."
                raise RuntimeError(msg)

        self._search_timer = Timer(time_for_move / 1000.0, self._timeout.set)
        self._search_timer.start()

    def _search(self, board: Board, max_depth: int) -> None:
        """
        Search for the best move and report info to stdout.
        :param board: current board representation
        :param max_depth: limit for depth of iterative search
        """
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            print("bestmove 0000", flush=True)
            return

        # Start with a legal move in case search stops before depth 1 completes.
        moves: list[Move] = [choice(legal_moves)]
        depth = 0
        search_started = time() - 0.0001
        self._nodes_searched = 0

        while depth < max_depth:
            depth += 1
            try:
                evaluation, moves = self._negamax(board, depth, float("-inf"), float("inf"))
            except RuntimeError:
                break

            current_time = time() - search_started
            print(
                f"info depth {depth} score cp {int(evaluation)} "
                f"nodes {self._nodes_searched} nps {int(self._nodes_searched / current_time)} "
                f"time {round(1000 * current_time)} "
                f"pv {' '.join([move.uci() for move in moves])}",
                flush=True,
            )

        if self._search_timer is not None:
            self._search_timer.cancel()
            self._search_timer = None
        print(f"bestmove {moves[0].uci()}", flush=True)

    def _negamax(
        self, board: Board, depth: int, alpha: float, beta: float
    ) -> tuple[float, list[Move]]:
        """
        Depth-first search with pruning.
        :param board: chess board representation
        :param depth: allowed depth for deepening
        :param alpha: search parameter alpha
        :param beta: search parameter beta
        :return: evaluation, the best move continuation from the given position
        """
        self._check_stop()
        self._nodes_searched += 1

        if board.is_game_over():
            return self._heuristic.evaluate_result(board, depth), []
        if board.is_repetition() or board.is_fifty_moves():
            return 0.0, []
        if depth == 0:
            if getattr(self._heuristic, "use_quiescence", lambda: True)():
                return self._quiescence(board, alpha, beta), []
            return self._heuristic.evaluate_position(board), []

        original_alpha = alpha
        best_score = float("-inf")
        best_moves: list[Move] = []
        tt_entry = self._probe_tt(board, depth, alpha, beta)
        if tt_entry is not None:
            return tt_entry

        tt_move = self._tt.get(self._position_key(board))
        for move in self._order_moves(
            board,
            board.legal_moves,
            hash_move=tt_move.best_move if tt_move is not None else None,
        ):
            board.push(move)
            evaluation, moves = self._negamax(board, depth - 1, -beta, -alpha)
            board.pop()

            evaluation *= -1
            moves.insert(0, move)
            if evaluation > best_score:
                best_score = evaluation
                best_moves = moves

            if evaluation >= beta:
                self._store_tt(board, depth, evaluation, "lower", move)
                return evaluation, moves
            if evaluation > alpha:
                alpha = evaluation

        if not best_moves:
            return alpha, []

        bound = "exact" if alpha > original_alpha else "upper"
        self._store_tt(board, depth, alpha, bound, best_moves[0])
        return best_score, best_moves

    def _quiescence(self, board: Board, alpha: float, beta: float) -> float:
        """
        Quiescence search checks all possible captures and checks to ensure not returning
        evaluation of position in-between captures or lost after a simple check.
        :param board: chess board representation
        :param alpha: search parameter alpha
        :param beta: search parameter beta
        :return: evaluation
        """
        self._check_stop()

        if board.is_game_over():
            return self._heuristic.evaluate_result(board, -1)
        if board.is_repetition() or board.is_fifty_moves():
            return 0.0

        in_check = board.is_check()
        best_score = float("-inf")

        use_delta_pruning = False
        evaluation = float("-inf")

        if in_check:
            moves = self._order_moves(board, board.legal_moves)
        else:
            evaluation = self._heuristic.evaluate_position(board)
            best_score = evaluation

            if evaluation >= beta:
                return evaluation

            use_delta_pruning = len(board.piece_map()) > 8
            if use_delta_pruning and evaluation < alpha - PieceValues.QUEEN_VALUE:
                return evaluation

            alpha = max(alpha, evaluation)
            moves = self._get_quiescence_moves(board)

        for move in moves:
            if use_delta_pruning and board.is_capture(move):
                captured_piece = (
                    PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
                )
                piece_value = PieceValues.as_dict().get(captured_piece, 0) + 200
                if evaluation + piece_value < alpha:
                    continue

            board.push(move)
            score = -self._quiescence(board, -beta, -alpha)
            board.pop()
            self._nodes_searched += 1
            best_score = max(best_score, score)

            if score >= beta:
                return score
            alpha = max(alpha, score)

        return best_score if best_score != float("-inf") else alpha

    def _get_quiescence_moves(self, board: Board) -> Iterator[Move]:
        """
        Generate quiescence moves.
        :param board: chess board representation
        :return: tactical moves from the current position
        """
        return self._order_moves(
            board,
            iter(
                move
                for move in board.legal_moves
                if board.is_capture(move) or move.promotion
            ),
        )

    @staticmethod
    def _position_key(board: Board) -> tuple[object, ...]:
        return board._transposition_key()

    def _probe_tt(
        self, board: Board, depth: int, alpha: float, beta: float
    ) -> tuple[float, list[Move]] | None:
        entry = self._tt.get(self._position_key(board))
        if entry is None or entry.depth < depth:
            return None

        if entry.bound == "exact":
            return entry.score, [entry.best_move] if entry.best_move is not None else []
        if entry.bound == "lower" and entry.score >= beta:
            return entry.score, [entry.best_move] if entry.best_move is not None else []
        if entry.bound == "upper" and entry.score <= alpha:
            return entry.score, [entry.best_move] if entry.best_move is not None else []
        return None

    def _store_tt(
        self, board: Board, depth: int, score: float, bound: str, best_move: Move | None
    ) -> None:
        key = self._position_key(board)
        current = self._tt.get(key)
        if current is None or depth >= current.depth:
            self._tt[key] = TranspositionEntry(depth, score, bound, best_move)

    @staticmethod
    def _order_moves(
        board: Board, moves: Iterable[Move], hash_move: Move | None = None
    ) -> Iterator[Move]:
        scored_moves: list[tuple[Move, float]] = []
        for move in moves:
            score = 0.0

            if hash_move is not None and move == hash_move:
                score += 1_000_000

            if board.is_capture(move):
                victim_piece = PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
                attacker_piece = board.piece_at(move.from_square)
                if victim_piece is not None and attacker_piece is not None:
                    score += PieceValues.as_dict().get(victim_piece, 0) * 10 - PieceValues.as_dict().get(
                        attacker_piece.piece_type, 0
                    )

            if move.promotion:
                score += PieceValues.as_dict().get(move.promotion, 0) * 5

            if board.gives_check(move):
                score += 50

            scored_moves.append((move, score))

        scored_moves.sort(key=operator.itemgetter(1), reverse=True)
        return iter(x[0] for x in scored_moves)
