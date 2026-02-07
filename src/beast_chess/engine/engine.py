import queue
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import IntEnum
from multiprocessing import Event, Queue
from random import choice
from threading import Timer
from time import time

import chess
import chess.polyglot
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

# A null move in UCI is represented as "0000".
# python-chess provides Move.null() for this.\
# See: chess.Move.null() in the core docs.\
# https://python-chess.readthedocs.io/en/latest/core.html\
NULL_MOVE = Move.null()

# Use a large finite bound rather than +/-inf to keep everything as plain numbers.
INF = 1_000_000_000


class _TTBound(IntEnum):
    EXACT = 0
    LOWER = 1
    UPPER = 2


@dataclass(slots=True)
class _TTEntry:
    depth: int
    score: float
    bound: _TTBound
    best_move: Move | None


class Engine:
    """UCI search worker.

    The code is intentionally single-threaded inside the search (the engine runs as a separate
    process already)."""

    # --- Search tuning (keep small; python overhead dominates) ---
    _TT_MAX_SIZE = 750_000  # dict entries; cleared when exceeded

    # Aspiration window (centipawns-ish). If heuristic is NN and uses floats, this is still fine.
    _ASPIRATION_WINDOW = 60

    # Null-move reduction.
    _NULL_REDUCTION_BASE = 2
    _NULL_REDUCTION_DEEP = 3

    def __init__(self, queue: Queue) -> None:
        self._heuristic: Heuristic | None = None
        self._nodes_searched = 0
        self._queue = queue
        self._timeout = Event()

        # Timer management: without cancelling, old timers can fire during later searches.
        self._timer: Timer | None = None

        # If a quit command is received during search we need to terminate after returning.
        self._quit_requested = False

        # Transposition table + move ordering helpers.
        self._tt: dict[int, _TTEntry] = {}
        self._killers: list[list[Move | None]] = []  # [ply][0..1]
        self._history: dict[int, int] = {}

        # Cache piece values once (PieceValues.as_dict() allocates a dict).
        values = PieceValues.as_dict()
        # 1..6 (pawn..king). King value is usually irrelevant for MVV-LVA.
        self._piece_value: list[int] = [0] * 7
        for pt, val in values.items():
            if 0 <= pt < len(self._piece_value):
                self._piece_value[pt] = int(val)

    def start(self) -> None:
        """Start the engine process, wait for EngineCommand and search for the best move."""
        while True:
            command: EngineCommand = self._queue.get()

            if command.quit:
                break
            if command.stop:
                continue

            self._quit_requested = False
            self._heuristic = self._choose_heuristic(command.search_options)
            self._start_timer(command.search_options)
            self._search(command.search_options.board, command.search_options.depth)

            if self._quit_requested:
                break

    # ------------------------
    # Stop / time handling
    # ------------------------

    def _check_stop(self) -> None:
        """Check if stop conditions were met and abort search by raising RuntimeError."""
        if self._timeout.is_set():
            raise RuntimeError("Time-out")

        # multiprocessing.Queue.empty() is not reliable. Try a non-blocking read instead.
        try:
            command = self._queue.get_nowait()
        except queue.Empty:
            return

        if command.quit:
            self._quit_requested = True
            raise RuntimeError("Quit requested")

        if command.stop:
            raise RuntimeError("Stop requested")

        # Not a stop/quit command. Put it back so the main loop can handle it.
        self._queue.put(command)

    # ------------------------
    # Heuristic selection
    # ------------------------

    @staticmethod
    def _choose_heuristic(search_options: SearchOptions) -> Heuristic:
        """Initialize a heuristic function based on search parameters."""
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
            raise RuntimeError("Warning: incorrect model file.")

        if search_options.heuristic_type == HeuristicType.NEURAL_NETWORK:
            return NeuralNetwork(
                model_file=search_options.model_file,
                fifty_moves_rule=search_options.fifty_moves_rule,
                syzygy_path=search_options.syzygy_path,
                syzygy_probe_limit=search_options.syzygy_probe_limit,
                threads=search_options.threads,
            )

        return classical_heuristic

    # ------------------------
    # Time allocation
    # ------------------------

    def _start_timer(self, search_options: SearchOptions) -> None:
        """Start (or clear) the search timer, based on time controls."""
        self._timeout.clear()

        # Cancel any previous timer to avoid it firing in a later search.
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

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
                raise RuntimeError("Incorrect time options.")

        # Guard against negative/zero times.
        time_for_move = max(1.0, float(time_for_move))

        self._timer = Timer(time_for_move / 1000.0, self._timeout.set)
        self._timer.daemon = True
        self._timer.start()

    # ------------------------
    # Root search / UCI output
    # ------------------------

    def _search(self, board: Board, max_depth: int) -> None:
        """Iterative deepening + alpha-beta search."""
        # Root legal moves: if none, report a null move (UCI uses 0000).
        root_moves = list(board.legal_moves)
        if not root_moves:
            print("bestmove 0000", flush=True)
            return

        # Fallback random move (used if we time out before finishing depth 1).
        best_line: list[Move] = [choice(root_moves)]
        best_score: float = 0.0

        # Move ordering helpers depend on max search depth.
        self._killers = [[None, None] for _ in range(max_depth + 64)]
        self._history.clear()

        search_started = time() - 0.0001
        self._nodes_searched = 0

        aspiration = float(self._ASPIRATION_WINDOW)

        for depth in range(1, max_depth + 1):
            # Aspiration windows: start narrow after depth 1.
            if depth == 1:
                alpha, beta = -INF, INF
            else:
                alpha = best_score - aspiration
                beta = best_score + aspiration

            while True:
                try:
                    score, line = self._negamax(board, depth, alpha, beta, ply=0, allow_null=True)
                except RuntimeError:
                    # Search aborted (timeout/stop/quit). Use the last completed best line.
                    self._cancel_timer()
                    print(f"bestmove {best_line[0].uci()}", flush=True)
                    return

                # Fail-low: widen window down.
                if score <= alpha:
                    alpha = -INF
                    beta = score + aspiration
                    aspiration *= 2
                    continue

                # Fail-high: widen window up.
                if score >= beta:
                    alpha = score - aspiration
                    beta = INF
                    aspiration *= 2
                    continue

                # Inside window: accept.
                best_score, best_line = score, (line if line else best_line)
                aspiration = float(self._ASPIRATION_WINDOW)
                break

            current_time = time() - search_started
            nps = int(self._nodes_searched / current_time) if current_time > 0 else 0

            print(
                f"info depth {depth} score cp {int(best_score)} "
                f"nodes {self._nodes_searched} nps {nps} "
                f"time {round(1000 * current_time)} "
                f"pv {' '.join([m.uci() for m in best_line])}",
                flush=True,
            )

        self._cancel_timer()
        print(f"bestmove {best_line[0].uci()}", flush=True)

    def _cancel_timer(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    # ------------------------
    # Alpha-beta with enhancements
    # ------------------------

    @staticmethod
    def _move_key(move: Move) -> int:
        """Compact move key for history heuristic."""
        promo = move.promotion or 0
        return move.from_square | (move.to_square << 6) | (promo << 12)

    def _tt_store(self, key: int, depth: int, score: float, bound: _TTBound, best_move: Move | None) -> None:
        if len(self._tt) > self._TT_MAX_SIZE:
            self._tt.clear()
        self._tt[key] = _TTEntry(depth=depth, score=score, bound=bound, best_move=best_move)

    def _negamax(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        *,
        ply: int,
        allow_null: bool,
    ) -> tuple[float, list[Move]]:
        """Negamax alpha-beta search.

        Enhancements implemented here:
          - Transposition table (Polyglot Zobrist hash)
          - Aspiration windows (handled at root)
          - Killer move heuristic
          - History heuristic
          - Null-move pruning
        """
        self._check_stop()
        self._nodes_searched += 1

        key = chess.polyglot.zobrist_hash(board)
        tt_entry = self._tt.get(key)
        tt_move = tt_entry.best_move if tt_entry is not None else None

        # Terminal/draw conditions.
        if board.is_game_over():
            return self._heuristic.evaluate_result(board, depth), []
        if board.is_fifty_moves() or board.is_repetition():
            return 0.0, []

        # Transposition table cutoffs.
        if tt_entry is not None and tt_entry.depth >= depth:
            if tt_entry.bound == _TTBound.EXACT:
                return tt_entry.score, [tt_entry.best_move] if tt_entry.best_move else []
            if tt_entry.bound == _TTBound.LOWER and tt_entry.score >= beta:
                return tt_entry.score, [tt_entry.best_move] if tt_entry.best_move else []
            if tt_entry.bound == _TTBound.UPPER and tt_entry.score <= alpha:
                return tt_entry.score, [tt_entry.best_move] if tt_entry.best_move else []

        # Leaf.
        if depth == 0:
            if self._heuristic.use_quiescence():
                return self._quiescence(board, alpha, beta, ply=ply), []
            return float(self._heuristic.evaluate_position(board)), []

        # Null-move pruning (avoid in check to keep legality, and avoid likely zugzwang endgames).
        if allow_null and depth >= 3 and not board.is_check() and self._null_move_allowed(board):
            reduction = self._NULL_REDUCTION_DEEP if depth >= 7 else self._NULL_REDUCTION_BASE
            board.push(NULL_MOVE)
            null_score, _ = self._negamax(
                board,
                depth - 1 - reduction,
                -beta,
                -beta + 1,
                ply=ply + 1,
                allow_null=False,
            )
            board.pop()
            null_score = -null_score

            if null_score >= beta:
                # Lower bound.
                self._tt_store(key, depth, null_score, _TTBound.LOWER, tt_move)
                return null_score, []

        orig_alpha = alpha
        best_score = -INF
        best_line: list[Move] = []
        best_move: Move | None = None

        moves = list(board.legal_moves)
        if not moves:
            # Should be covered by is_game_over(), but keep robust.
            return self._heuristic.evaluate_result(board, depth), []

        for move in self._order_moves(board, moves, tt_move=tt_move, ply=ply):
            is_capture = board.is_capture(move)

            board.push(move)
            score, child_line = self._negamax(
                board,
                depth - 1,
                -beta,
                -alpha,
                ply=ply + 1,
                allow_null=True,
            )
            board.pop()

            score = -score
            line = [move, *child_line]

            if score > best_score:
                best_score = score
                best_line = line
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                # Beta cutoff -> update move ordering heuristics for *quiet* moves.
                if not is_capture and move.promotion is None:
                    self._store_killer(move, ply)
                    self._history_update(move, depth)

                break

        # Store in TT.
        if best_score <= orig_alpha:
            bound = _TTBound.UPPER
        elif best_score >= beta:
            bound = _TTBound.LOWER
        else:
            bound = _TTBound.EXACT

        self._tt_store(key, depth, best_score, bound, best_move)
        return best_score, best_line

    def _null_move_allowed(self, board: Board) -> bool:
        """Heuristic guard for null-move pruning.

        Null-move can be unsafe in zugzwang-y endgames. Keep this cheap."""
        # If either side still has a queen or rook, zugzwang is much less likely.
        if board.queens or board.rooks:
            return True

        # If there are only kings + pawns/minors, be conservative.
        # Allow null-move only if there are still multiple minors on board.
        minor_count = int(board.knights.bit_count() + board.bishops.bit_count())
        return minor_count >= 2

    def _store_killer(self, move: Move, ply: int) -> None:
        killers = self._killers[ply]
        if killers[0] != move:
            killers[1] = killers[0]
            killers[0] = move

    def _history_update(self, move: Move, depth: int) -> None:
        key = self._move_key(move)
        self._history[key] = self._history.get(key, 0) + depth * depth

    def _order_moves(
        self, board: Board, moves: Iterable[Move], *, tt_move: Move | None, ply: int
    ) -> Iterator[Move]:
        """Order moves using TT move, MVV-LVA, killer moves and history heuristic."""
        killers = self._killers[ply]
        killer1, killer2 = killers[0], killers[1]

        def score_move(move: Move) -> int:
            score = 0

            if tt_move is not None and move == tt_move:
                return 1_000_000_000

            if board.is_capture(move):
                victim = (
                    PAWN if board.is_en_passant(move) else (board.piece_type_at(move.to_square) or 0)
                )
                attacker = board.piece_type_at(move.from_square) or 0
                score += 400_000
                score += self._piece_value[victim] * 10 - self._piece_value[attacker]

                if move.promotion:
                    score += self._piece_value[move.promotion] * 5
            else:
                if killer1 is not None and move == killer1:
                    score += 300_000
                elif killer2 is not None and move == killer2:
                    score += 290_000
                else:
                    score += self._history.get(self._move_key(move), 0)

            if board.gives_check(move):
                score += 50

            return score

        scored = [(m, score_move(m)) for m in moves]
        scored.sort(key=lambda x: x[1], reverse=True)
        return (m for (m, _) in scored)

    # ------------------------
    # Quiescence
    # ------------------------

    def _quiescence(self, board: Board, alpha: float, beta: float, *, ply: int) -> float:
        """Quiescence search: search captures and checks."""
        self._check_stop()
        self._nodes_searched += 1

        if board.is_game_over():
            return float(self._heuristic.evaluate_result(board, 0))
        if board.is_fifty_moves() or board.is_repetition():
            return 0.0

        stand_pat = float(self._heuristic.evaluate_position(board))

        # Fail-soft.
        if stand_pat >= beta:
            return stand_pat

        use_delta_pruning = board.occupied.bit_count() > 8
        if use_delta_pruning and stand_pat < alpha - float(self._piece_value[chess.QUEEN]):
            return alpha

        if stand_pat > alpha:
            alpha = stand_pat

        moves = [m for m in board.legal_moves if board.is_capture(m) or board.gives_check(m)]
        if not moves:
            return alpha

        # Order tacticals by MVV-LVA (+ checks).
        ordered = list(self._order_moves(board, moves, tt_move=None, ply=ply))

        for move in ordered:
            if use_delta_pruning and board.is_capture(move):
                captured = PAWN if board.is_en_passant(move) else (board.piece_type_at(move.to_square) or 0)
                gain = float(self._piece_value[captured] + 200)
                if stand_pat + gain < alpha:
                    continue

            board.push(move)
            score = -self._quiescence(board, -beta, -alpha, ply=ply + 1)
            board.pop()

            if score >= beta:
                return score

            if score > alpha:
                alpha = score

        return alpha
