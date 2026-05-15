import operator
from dataclasses import dataclass
from queue import Queue
from threading import Event, Timer
from time import time

from beast_chess.board import (
    BISHOP,
    CAPTURE,
    EN_PASSANT,
    KING,
    KNIGHT,
    NO_PIECE,
    NULL_MOVE,
    PAWN,
    PROMOTION,
    QUEEN,
    ROOK,
    Board,
    Move,
    piece_type,
    same_move,
    uci,
)
from beast_chess.heuristics import (
    ClassicalHeuristic,
    Heuristic,
    HeuristicType,
    NeuralNetwork,
    PieceValues,
    RandomHeuristic,
)
from beast_chess.infra import Constants, EngineCommand, SearchOptions

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2
MAX_PLY = 128
MAX_TT_SIZE = 1_000_000
ASPIRATION_WINDOW = 50
MATE_THRESHOLD = 250_000
FUTILITY_MARGIN = 160
REVERSE_FUTILITY_MARGIN = 120
PIECE_VALUE_BY_TYPE = (
    0,
    PieceValues.PAWN_VALUE,
    PieceValues.KNIGHT_VALUE,
    PieceValues.BISHOP_VALUE,
    PieceValues.ROOK_VALUE,
    PieceValues.QUEEN_VALUE,
    0,
)
CHECK_STOP_INTERVAL = 2047
TACTICAL_FLAGS = CAPTURE | PROMOTION


@dataclass(slots=True)
class _TranspositionEntry:
    key: int
    depth: int
    score: float
    bound: int
    move: Move
    static_eval: float | None


class Engine:
    def __init__(self, queue: Queue) -> None:
        self._heuristic: Heuristic | None = None
        self._nodes_searched = 0
        self._queue = queue
        self._timeout = Event()
        self._transposition_table: dict[int, _TranspositionEntry] = {}
        self._killer_moves: list[list[Move]] = [[NULL_MOVE, NULL_MOVE] for _ in range(MAX_PLY)]
        self._history_heuristic = [0] * (64 * 64)

    def start(self) -> None:
        """
        Start the engine process, wait for EngineCommand, and search for the best move.
        """
        while True:
            # check queue for command
            command: EngineCommand = self._queue.get()

            if command.quit:
                break
            if command.stop:
                continue

            try:
                self._heuristic = self._choose_heuristic(command.search_options)
            except RuntimeError as err:
                print(f"info string {err}", flush=True)
                continue
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
        if search_options.heuristic_type == HeuristicType.CLASSICAL:
            return ClassicalHeuristic()

        if search_options.heuristic_type == HeuristicType.RANDOM:
            search_options.depth = 1
            return RandomHeuristic()

        if search_options.heuristic_type == HeuristicType.NEURAL_NETWORK:
            model_path = Constants.resolve_model_path(search_options.model_file)
            if model_path is None:
                msg = f"Model file '{search_options.model_file}' was not found."
                raise RuntimeError(msg)

            return NeuralNetwork(
                model_file=model_path,
                threads=search_options.threads,
            )

        msg = f"Unknown heuristic type: {search_options.heuristic_type}"
        raise RuntimeError(msg)

    def _start_timer(self, search_options: SearchOptions) -> None:
        """
        Check search options and start the timer if there is limited time for the best move search.
        :param search_options: search parameters
        """
        self._timeout.clear()

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

        timer = Timer(time_for_move / 1000.0, self._timeout.set)
        timer.start()

    def _search(self, board: Board, max_depth: int) -> None:
        """
        Search for the best move and report info to stdout.
        :param board: current board representation
        :param max_depth: limit for depth of iterative search
        """
        # Keep a legal fallback in case timeout stops before depth one completes.
        legal_moves = board.generate_legal_moves()
        moves: list[Move] = [legal_moves[0]] if legal_moves else []
        depth = 0
        evaluation = 0.0
        search_started = time() - 0.0001
        self._nodes_searched = 0
        self._reset_search_tables()

        while depth < max_depth:
            depth += 1
            try:
                evaluation, moves = self._search_depth(board, depth, evaluation, moves)
            except RuntimeError:
                break

            current_time = time() - search_started
            print(
                f"info depth {depth} score cp {int(evaluation)} "
                f"nodes {self._nodes_searched} nps {int(self._nodes_searched / current_time)} "
                f"time {round(1000 * current_time)} "
                f"pv {' '.join(uci(move) for move in moves)}",
                flush=True,
            )

        print(f"bestmove {uci(moves[0]) if moves else '0000'}", flush=True)

    def _search_depth(
        self,
        board: Board,
        depth: int,
        previous_score: float,
        previous_line: list[Move],
    ) -> tuple[float, list[Move]]:
        if depth == 1:
            return self._negamax(board, depth, float("-inf"), float("inf"))

        window = ASPIRATION_WINDOW
        alpha = previous_score - window
        beta = previous_score + window
        best_score = previous_score
        best_line = previous_line

        while True:
            score, line = self._negamax(board, depth, alpha, beta)
            if score <= alpha:
                alpha -= window
                window *= 2
                continue
            if score >= beta:
                beta += window
                window *= 2
                continue
            best_score = score
            best_line = line or best_line
            break

        return best_score, best_line

    def _negamax(  # noqa: C901, PLR0911, PLR0912, PLR0914, PLR0915
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        ply: int = 0,
        *,
        allow_null: bool = True,
        is_pv: bool = True,
    ) -> tuple[float, list[Move]]:
        """
        Depth-first search with pruning.
        :param board: chess board representation
        :param depth: allowed depth for deepening
        :param alpha: search parameter alpha
        :param beta: search parameter beta
        :return: evaluation, the best move continuation from the given position
        """
        self._nodes_searched += 1
        if self._nodes_searched & CHECK_STOP_INTERVAL == 0:
            self._check_stop()

        if board.is_repetition() or board.is_fifty_moves():
            return 0.0, []

        alpha = max(alpha, self._heuristic.loss_value + ply)
        beta = min(beta, self._heuristic.win_value - ply)
        if alpha >= beta:
            return alpha, []

        if depth == 0:
            return self._quiescence(board, alpha, beta), []

        alpha_original = alpha
        key = board.zobrist_key
        entry = self._transposition_table.get(key)
        tt_move = NULL_MOVE
        static_eval = None
        if entry is not None and entry.key == key:
            tt_move = entry.move
            static_eval = entry.static_eval
            if entry.depth >= depth and not is_pv:
                tt_score = self._score_from_tt(entry.score, ply)
                if entry.bound == TT_EXACT:
                    return tt_score, [entry.move] if entry.move != NULL_MOVE else []
                if entry.bound == TT_LOWER and tt_score >= beta:
                    return tt_score, [entry.move] if entry.move != NULL_MOVE else []
                if entry.bound == TT_UPPER and tt_score <= alpha:
                    return tt_score, []
                if entry.bound == TT_LOWER:
                    alpha = max(alpha, tt_score)
                elif entry.bound == TT_UPPER:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score, [entry.move] if entry.move != NULL_MOVE else []

        in_check = board.is_check()

        if static_eval is None and not in_check and (depth <= 3 or allow_null):
            static_eval = self._heuristic.evaluate_position(board)

        if (
            not is_pv
            and not in_check
            and depth <= 3
            and static_eval is not None
            and static_eval - REVERSE_FUTILITY_MARGIN * depth >= beta
        ):
            return static_eval, []

        can_try_null = allow_null and not is_pv and not in_check
        null_margin_ok = depth >= 3 and static_eval is not None and static_eval >= beta
        if can_try_null and null_margin_ok and self._can_null_move(board):
            reduction = 2 + depth // 4
            board.push_null()
            try:
                null_score, _ = self._negamax(
                    board,
                    max(0, depth - reduction - 1),
                    -beta,
                    -beta + 1,
                    ply + 1,
                    allow_null=False,
                    is_pv=False,
                )
            finally:
                board.pop()
            if -null_score >= beta:
                return beta, []

        if tt_move == NULL_MOVE and is_pv and depth >= 4:
            self._negamax(
                board,
                depth - 2,
                alpha,
                beta,
                ply,
                allow_null=False,
                is_pv=False,
            )
            entry = self._transposition_table.get(key)
            if entry is not None and entry.key == key:
                tt_move = entry.move

        legal_moves = board.generate_legal_moves()
        if not legal_moves:
            terminal_score = self._heuristic.loss_value + ply if in_check else 0.0
            return terminal_score, []

        best_moves: list[Move] = []
        best_move = NULL_MOVE
        best_score = float("-inf")
        searched_moves = 0
        futility_base = (
            static_eval + FUTILITY_MARGIN * depth
            if static_eval is not None and not in_check and not is_pv and depth <= 2
            else None
        )

        for move in self._order_moves(board, legal_moves, tt_move, ply):
            move_value = int(move)
            flags = move_value >> 15
            is_quiet = (flags & TACTICAL_FLAGS) == 0

            if (
                futility_base is not None
                and is_quiet
                and searched_moves > 0
                and futility_base <= alpha
            ):
                continue

            board.push(move)
            try:
                gives_check = board.is_check()
                extension = 1 if gives_check and depth <= 2 else 0
                next_depth = depth - 1 + extension

                reduction = 0
                can_reduce_late_move = searched_moves >= 4 and is_quiet and depth >= 3
                reduction_is_safe = not is_pv and not in_check and not gives_check
                if can_reduce_late_move and reduction_is_safe:
                    reduction = 1 + depth // 6 + searched_moves // 12

                if searched_moves == 0:
                    child_score, child_line = self._negamax(
                        board,
                        next_depth,
                        -beta,
                        -alpha,
                        ply + 1,
                        allow_null=True,
                        is_pv=is_pv,
                    )
                    evaluation = -child_score
                    moves = child_line
                else:
                    reduced_depth = max(0, next_depth - reduction)
                    child_score, _ = self._negamax(
                        board,
                        reduced_depth,
                        -alpha - 1,
                        -alpha,
                        ply + 1,
                        allow_null=True,
                        is_pv=False,
                    )
                    evaluation = -child_score
                    moves = []
                    if reduction and evaluation > alpha:
                        child_score, _ = self._negamax(
                            board,
                            next_depth,
                            -alpha - 1,
                            -alpha,
                            ply + 1,
                            allow_null=True,
                            is_pv=False,
                        )
                        evaluation = -child_score
                    if alpha < evaluation < beta:
                        child_score, child_line = self._negamax(
                            board,
                            next_depth,
                            -beta,
                            -alpha,
                            ply + 1,
                            allow_null=True,
                            is_pv=True,
                        )
                        evaluation = -child_score
                        moves = child_line
            finally:
                board.pop()
            searched_moves += 1

            if evaluation > best_score:
                best_score = evaluation
                best_move = move
                best_moves = [move, *moves]

            if evaluation >= beta:
                if is_quiet:
                    self._record_quiet_cutoff(move, depth, ply)
                self._store_tt(key, depth, beta, TT_LOWER, move, ply, static_eval)
                return beta, []
            alpha = max(alpha, evaluation)

        if searched_moves == 0:
            return alpha, []

        bound = TT_EXACT if best_score > alpha_original else TT_UPPER
        self._store_tt(key, depth, alpha, bound, best_move, ply, static_eval)
        return alpha, best_moves

    def _quiescence(  # noqa: C901, PLR0911, PLR0912
        self, board: Board, alpha: float, beta: float
    ) -> float:
        """
        Quiescence search checks all possible captures and checks to ensure not returning
        evaluation of position in-between captures or lost after a simple check.
        :param board: chess board representation
        :param alpha: search parameter alpha
        :param beta: search parameter beta
        :return: evaluation
        """
        self._nodes_searched += 1
        if self._nodes_searched & CHECK_STOP_INTERVAL == 0:
            self._check_stop()

        if board.is_repetition() or board.is_fifty_moves():
            return 0.0

        if board.is_check():
            evasions = board.generate_legal_moves()
            if not evasions:
                return self._heuristic.evaluate_result(board, -1)

            for move in self._order_moves(board, evasions):
                board.push(move)
                try:
                    score = -self._quiescence(board, -beta, -alpha)
                finally:
                    board.pop()

                if score >= beta:
                    return beta
                alpha = max(alpha, score)
            return alpha

        evaluation = self._heuristic.evaluate_position(board)

        if evaluation >= beta:
            return beta

        use_delta_pruning = board.occupied.bit_count() > 8
        if use_delta_pruning and evaluation < alpha - PieceValues.QUEEN_VALUE:
            return alpha

        alpha = max(alpha, evaluation)

        for move in self._order_moves(board, board.generate_legal_captures()):
            if use_delta_pruning:
                piece_value = self._tactical_gain_upper_bound(board, move)
                losing_capture = self._static_exchange_evaluation(board, move) < 0
                if evaluation + piece_value < alpha or losing_capture:
                    continue

            board.push(move)
            try:
                score = -self._quiescence(board, -beta, -alpha)
            finally:
                board.pop()

            if score >= beta:
                return beta
            alpha = max(alpha, score)

        return alpha

    def _order_moves(  # noqa: C901
        self,
        board: Board,
        moves: list[Move],
        tt_move: Move = NULL_MOVE,
        ply: int = 0,
    ) -> list[Move]:
        if len(moves) < 2 and (
            tt_move == NULL_MOVE or not moves or not same_move(moves[0], tt_move)
        ):
            return moves

        scored_moves: list[tuple[int, Move]] = []
        for move in moves:
            score = 0
            move_value = int(move)
            target = (move_value >> 6) & 0x3F
            promotion = (move_value >> 12) & 0x7
            flags = move_value >> 15

            if tt_move != NULL_MOVE and same_move(move, tt_move):
                scored_moves.append((10_000_000, move))
                continue

            if flags & CAPTURE:
                victim_piece = PAWN if flags & EN_PASSANT else board.piece_at(target)
                attacker_piece = board.piece_at(move_value & 0x3F)
                if victim_piece != NO_PIECE and attacker_piece != NO_PIECE:  # noqa: PLR1714
                    score = (
                        1_000_000
                        + PIECE_VALUE_BY_TYPE[piece_type(victim_piece)] * 10
                        - PIECE_VALUE_BY_TYPE[piece_type(attacker_piece)]
                        + self._static_exchange_evaluation(board, move)
                    )

            if promotion != NO_PIECE:
                score += 900_000 + PIECE_VALUE_BY_TYPE[promotion] * 5

            if score == 0:
                killers = self._killer_moves[ply] if ply < MAX_PLY else None
                first_killer = killers[0] if killers is not None else NULL_MOVE
                second_killer = killers[1] if killers is not None else NULL_MOVE
                if first_killer != NULL_MOVE and same_move(move, first_killer):
                    score = 800_000
                elif second_killer != NULL_MOVE and same_move(move, second_killer):
                    score = 700_000
                else:
                    score = self._history_heuristic[((move_value & 0x3F) << 6) | target]

            scored_moves.append((score, move))

        if not any(score for score, _move in scored_moves):
            return moves

        scored_moves.sort(key=operator.itemgetter(0), reverse=True)
        return [move for _, move in scored_moves]

    @staticmethod
    def _tactical_gain_upper_bound(board: Board, move: Move) -> int:
        move_value = int(move)
        target = (move_value >> 6) & 0x3F
        promotion = (move_value >> 12) & 0x7
        flags = move_value >> 15
        gain = 200
        if flags & CAPTURE:
            captured_piece = PAWN if flags & EN_PASSANT else board.piece_type_at(target)
            gain += PIECE_VALUE_BY_TYPE[captured_piece]

        if promotion != NO_PIECE:
            gain += PIECE_VALUE_BY_TYPE[promotion]

        return gain

    def _static_exchange_evaluation(self, board: Board, move: Move) -> int:  # noqa: PLR0914
        move_value = int(move)
        source = move_value & 0x3F
        target = (move_value >> 6) & 0x3F
        promotion = (move_value >> 12) & 0x7
        flags = move_value >> 15
        moved_piece = board.piece_at(source)
        moved_piece_type = piece_type(moved_piece)
        target_piece = PAWN if flags & EN_PASSANT else board.piece_type_at(target)
        gain = [
            PIECE_VALUE_BY_TYPE[target_piece]
            + (PIECE_VALUE_BY_TYPE[promotion] - PIECE_VALUE_BY_TYPE[PAWN] if promotion else 0)
        ]
        piece_on_target = promotion or moved_piece_type
        occupied = board.occupied ^ (1 << source)
        if flags & EN_PASSANT:
            captured_square = target - 8 if board.side_to_move == 0 else target + 8
            occupied ^= 1 << captured_square
            occupied |= 1 << target
        elif (flags & CAPTURE) == 0:
            occupied |= 1 << target

        side = board.side_to_move ^ 1
        attackers = board.attackers_to(target, side, occupied) & occupied
        while attackers:
            attacker_type, attacker_bit = self._least_valuable_attacker(board, attackers, side)
            gain.append(PIECE_VALUE_BY_TYPE[piece_on_target] - gain[-1])
            if max(-gain[-2], gain[-1]) < 0:
                break
            occupied ^= attacker_bit
            piece_on_target = attacker_type
            side ^= 1
            attackers = board.attackers_to(target, side, occupied) & occupied

        for index in range(len(gain) - 2, -1, -1):
            gain[index] = max(gain[index], -gain[index + 1])
        return gain[0]

    @staticmethod
    def _least_valuable_attacker(board: Board, attackers: int, color: int) -> tuple[int, int]:
        for piece in (PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING):
            piece_attackers = attackers & board.pieces(piece, color)
            if piece_attackers:
                bit = piece_attackers & -piece_attackers
                return piece, bit
        return KING, attackers & -attackers

    def _record_quiet_cutoff(self, move: Move, depth: int, ply: int) -> None:
        if ply < MAX_PLY:
            killers = self._killer_moves[ply]
            if killers[0] == NULL_MOVE or not same_move(move, killers[0]):
                killers[1] = killers[0]
                killers[0] = move

        move_value = int(move)
        history_index = ((move_value & 0x3F) << 6) | ((move_value >> 6) & 0x3F)
        self._history_heuristic[history_index] += depth * depth
        if self._history_heuristic[history_index] > 1_000_000:
            self._history_heuristic = [score // 2 for score in self._history_heuristic]

    def _store_tt(  # noqa: PLR0917
        self,
        key: int,
        depth: int,
        score: float,
        bound: int,
        move: Move,
        ply: int,
        static_eval: float | None,
    ) -> None:
        if len(self._transposition_table) > MAX_TT_SIZE:
            self._transposition_table.clear()

        current = self._transposition_table.get(key)
        if current is not None and current.depth > depth:
            return

        self._transposition_table[key] = _TranspositionEntry(
            key=key,
            depth=depth,
            score=self._score_to_tt(score, ply),
            bound=bound,
            move=move,
            static_eval=static_eval,
        )

    @staticmethod
    def _score_to_tt(score: float, ply: int) -> float:
        if score > MATE_THRESHOLD:
            return score + ply
        if score < -MATE_THRESHOLD:
            return score - ply
        return score

    @staticmethod
    def _score_from_tt(score: float, ply: int) -> float:
        if score > MATE_THRESHOLD:
            return score - ply
        if score < -MATE_THRESHOLD:
            return score + ply
        return score

    @staticmethod
    def _can_null_move(board: Board) -> bool:
        side = board.side_to_move
        return bool(
            board.pieces(KNIGHT, side)
            | board.pieces(BISHOP, side)
            | board.pieces(ROOK, side)
            | board.pieces(QUEEN, side)
        )

    def _reset_search_tables(self) -> None:
        self._transposition_table.clear()
        self._killer_moves = [[NULL_MOVE, NULL_MOVE] for _ in range(MAX_PLY)]
        self._history_heuristic = [0] * (64 * 64)
