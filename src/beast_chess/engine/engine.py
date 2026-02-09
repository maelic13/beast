"""beast_chess engine search.

This file has been upgraded with several common chess-engine search techniques:

Search upgrades:
- Transposition table (TT) with PV move storage
- Aspiration windows in iterative deepening
- Principal Variation Search (PVS / NegaScout)
- Killer moves + History heuristic for move ordering
- Null-move pruning (with a simple zugzwang guard)
- Late Move Reductions (LMR)
- Check extensions (depth extension when giving check)
- Incremental repetition tracking (3-fold repetition detection without calling board.is_repetition() every node)
- Simple SEE-like capture filter ("SEE-lite") used for ordering/pruning obviously losing captures

The implementation is intentionally conservative and pure-Python (no extra dependencies),
compatible with python-chess ~= 1.11.

"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from multiprocessing import Event, Queue
from queue import Empty
from random import choice
from threading import Timer
from time import time
from typing import Iterable, Iterator

import chess
import chess.polyglot

from beast_chess.heuristics import (
    ClassicalHeuristic,
    Heuristic,
    HeuristicType,
    NeuralNetwork,
    PieceValues,
    RandomHeuristic,
)
from beast_chess.infra import Constants, EngineCommand, SearchOptions


class _TTFlag(IntEnum):
    EXACT = 0
    LOWER = 1
    UPPER = 2


@dataclass(slots=True)
class _TTEntry:
    key: int
    depth: int
    score: int
    flag: _TTFlag
    best_move: chess.Move | None
    generation: int


class Engine:
    # A practical safety cap. In Python, a dict of millions of entries is RAM-heavy.
    _TT_MAX_ENTRIES = 250_000

    # Hard cap to avoid unbounded killer array growth when user asks for very deep searches.
    _MAX_PLY = 128

    # How often (in nodes) we check time/stop flags. Higher = faster, but less responsive.
    _STOP_CHECK_PERIOD = 2048

    def __init__(self, queue: Queue) -> None:
        self._heuristic: Heuristic | None = None
        self._nodes_searched = 0
        self._queue = queue
        self._timeout = Event()

        # Search state (re-initialized per search)
        self._tt: dict[int, _TTEntry] = {}
        self._tt_generation = 0

        self._killers: list[list[chess.Move | None]] = []
        self._history: list[int] = []  # 2 * 64 * 64

        # Repetition tracking (per search)
        self._rep_counts: dict[int, int] = {}
        self._key_stack: list[int] = []

        # Root PV helper
        self._root_best_move: chess.Move | None = None

    def start(self) -> None:
        """Start the engine process, wait for EngineCommand and search for the best move when required."""
        while True:
            command: EngineCommand = self._queue.get()

            if command.quit:
                break
            if command.stop:
                continue

            self._heuristic = self._choose_heuristic(command.search_options)
            self._start_timer(command.search_options)
            self._search(command.search_options.board, command.search_options.depth)

    # --------------------------
    # Stop / time management
    # --------------------------

    def _check_stop(self) -> None:
        """Stop calculation if time is up or a stop/quit command is received."""
        if self._timeout.is_set():
            raise RuntimeError("Time-out.")

        # Non-blocking drain (at most one message) to avoid queue growth.
        # Queue.empty() is not reliable across processes, so we use get_nowait() in try/except.
        try:
            command = self._queue.get_nowait()
        except Empty:
            return

        if getattr(command, "stop", False) or getattr(command, "quit", False):
            raise RuntimeError(f"Command: stop - {command.stop}, quit - {command.quit}")

    def _should_stop(self) -> bool:
        # This method is used in the hot path. Avoid queue operations here.
        return self._timeout.is_set()

    # --------------------------
    # Heuristic selection
    # --------------------------

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

    # --------------------------
    # Timer
    # --------------------------

    def _start_timer(self, search_options: SearchOptions) -> None:
        """Start the timer if there is limited time for the best move search."""
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
                raise RuntimeError("Incorrect time options.")

        # Note: we do not keep a reference to the timer thread; it will fire at most once.
        timer = Timer(time_for_move / 1000.0, self._timeout.set)
        timer.daemon = True
        timer.start()

    # --------------------------
    # Iterative deepening driver
    # --------------------------

    def _reset_search_state(self, board: chess.Board, max_depth: int) -> None:
        self._nodes_searched = 0
        self._root_best_move = None

        # New generation to avoid mixing old TT best moves too aggressively.
        self._tt_generation = (self._tt_generation + 1) & 0x7FFFFFFF
        if len(self._tt) > self._TT_MAX_ENTRIES:
            # Simple eviction policy: clear. (In Python, fancier schemes often cost more than they save.)
            self._tt.clear()

        # Two killers per ply.
        ply_cap = min(max_depth + 8, self._MAX_PLY)
        self._killers = [[None, None] for _ in range(ply_cap)]
        self._history = [0] * (2 * 64 * 64)

        # Incremental repetition tracking: seed with game history (board.move_stack).
        self._key_stack = self._build_history_key_stack(board)
        self._rep_counts = {}
        for k in self._key_stack:
            self._rep_counts[k] = self._rep_counts.get(k, 0) + 1

    @staticmethod
    def _build_history_key_stack(board: chess.Board) -> list[int]:
        """Build a polyglot-zobrist key stack from the start of the game to the current position.

        This is O(game_length) and is done once per search. During the search we keep it incremental.
        """
        # We need the full stack, so use a copy with its move stack.
        b = board.copy(stack=True)
        keys_rev: list[int] = []
        while True:
            keys_rev.append(chess.polyglot.zobrist_hash(b))
            if not b.move_stack:
                break
            b.pop()
        keys_rev.reverse()
        return keys_rev

    def _search(self, board: chess.Board, max_depth: int) -> None:
        """Search for the best move and report info to stdout."""
        if self._heuristic is None:
            raise RuntimeError("Heuristic was not initialized.")

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            # No legal move: checkmate or stalemate. UCI expects some move; "0000" is common.
            print("bestmove 0000", flush=True)
            return

        self._reset_search_state(board, max_depth)

        # A fallback in case we time out before completing depth 1.
        best_line: list[chess.Move] = [choice(legal_moves)]
        best_score = 0

        depth = 0
        start_t = time() - 1e-6  # avoid div by zero
        window = 50  # aspiration window in centipawns

        while depth < max_depth:
            depth += 1
            self._check_stop()

            # Aspiration around last iteration's score.
            alpha = max(-Constants.INFINITE, best_score - window) if depth > 1 else -Constants.INFINITE
            beta = min(Constants.INFINITE, best_score + window) if depth > 1 else Constants.INFINITE

            while True:
                try:
                    score, line = self._negamax_root(board, depth, alpha, beta)
                except RuntimeError:
                    # stop/timeout - keep last fully completed best line
                    depth -= 1
                    break

                # Aspiration fail-low/high -> widen and re-search.
                if score <= alpha:
                    alpha = -Constants.INFINITE
                    window = min(window * 2, 800)
                    continue
                if score >= beta:
                    beta = Constants.INFINITE
                    window = min(window * 2, 800)
                    continue

                best_score, best_line = score, line
                window = 50  # reset window after a successful aspiration
                break

            current_time = time() - start_t
            # Avoid division by zero in extreme stop cases.
            nps = int(self._nodes_searched / max(current_time, 1e-6))

            pv_uci = " ".join(m.uci() for m in best_line)
            print(
                f"info depth {max(depth, 1)} score cp {int(best_score)} "
                f"nodes {self._nodes_searched} nps {nps} "
                f"time {round(1000 * current_time)} pv {pv_uci}",
                flush=True,
            )

            if self._should_stop():
                break

        print(f"bestmove {best_line[0].uci()}", flush=True)

    def _negamax_root(
        self, board: chess.Board, depth: int, alpha: int, beta: int
    ) -> tuple[int, list[chess.Move]]:
        """Root search that returns a PV line."""
        key = chess.polyglot.zobrist_hash(board)

        tt_entry = self._tt.get(key)
        tt_move = tt_entry.best_move if tt_entry and tt_entry.best_move else None

        best_score = -Constants.INFINITE
        best_move: chess.Move | None = None
        best_pv: list[chess.Move] = []

        moves = list(board.legal_moves)
        moves.sort(key=lambda m: self._move_order_key(board, m, tt_move, ply=0), reverse=True)

        for i, move in enumerate(moves):
            board.push(move)
            self._push_rep(board)

            # Check extension
            ext = 1 if board.is_check() else 0
            new_depth = depth - 1 + ext

            score = -self._negamax(board, new_depth, -beta, -alpha, ply=1, allow_null=True)

            self._pop_rep(board)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move
                best_pv = [move] + self._extract_pv(board, move, depth)

            if score > alpha:
                alpha = score

            if alpha >= beta:
                break

        if best_move is None:
            # Should not happen because we checked legal_moves earlier, but keep safe.
            return 0, [choice(list(board.legal_moves))]

        self._root_best_move = best_move
        return best_score, best_pv

    # --------------------------
    # Core negamax with alpha-beta
    # --------------------------

    def _negamax(
        self,
        board: chess.Board,
        depth: int,
        alpha: int,
        beta: int,
        *,
        ply: int,
        allow_null: bool,
    ) -> int:
        # Periodic stop checks (hot path).
        if (self._nodes_searched & (self._STOP_CHECK_PERIOD - 1)) == 0:
            self._check_stop()

        self._nodes_searched += 1

        # Draws (threefold, 50-move rule)
        key = chess.polyglot.zobrist_hash(board)
        if self._rep_counts.get(key, 0) >= 3:
            return 0
        if board.is_fifty_moves():
            return 0

        if board.is_game_over():
            return int(self._heuristic.evaluate_result(board, ply))

        if depth <= 0:
            return self._quiescence(board, alpha, beta, ply=ply)

        # TT probe
        tt_entry = self._tt.get(key)
        tt_move = tt_entry.best_move if tt_entry and tt_entry.best_move else None
        if tt_entry and tt_entry.depth >= depth:
            tt_score = self._tt_score_to_search(tt_entry.score, ply)
            if tt_entry.flag == _TTFlag.EXACT:
                return tt_score
            if tt_entry.flag == _TTFlag.LOWER:
                alpha = max(alpha, tt_score)
            elif tt_entry.flag == _TTFlag.UPPER:
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score

        in_check = board.is_check()

        # Null-move pruning (avoid in check and try to avoid pawn-only zugzwangs).
        if allow_null and depth >= 3 and not in_check and self._can_null_move(board):
            # A conservative reduction. (Depth - 1 - R)
            R = 2 + (depth >= 6)
            board.push(chess.Move.null())
            self._push_rep(board)

            score = -self._negamax(board, depth - 1 - R, -beta, -beta + 1, ply=ply + 1, allow_null=False)

            self._pop_rep(board)
            board.pop()

            if score >= beta:
                return beta

        # Move generation + ordering
        moves = list(board.legal_moves)
        if not moves:
            # No legal moves => mate or stalemate. python-chess game_over covers, but keep safe.
            return int(self._heuristic.evaluate_result(board, ply))

        moves.sort(key=lambda m: self._move_order_key(board, m, tt_move, ply=ply), reverse=True)

        best_score = -Constants.INFINITE
        best_move: chess.Move | None = None
        original_alpha = alpha

        # PVS / LMR loop
        for move_index, move in enumerate(moves):
            is_capture = board.is_capture(move)

            # SEE-lite pruning of obviously losing captures deep in the tree.
            if is_capture and depth >= 2 and move_index >= 4:
                if not self._see_ge(board, move, threshold=0):
                    # Losing capture, don't bother at this depth (still could be explored in quiescence).
                    continue

            board.push(move)
            self._push_rep(board)

            gives_check = board.is_check()
            ext = 1 if gives_check else 0
            new_depth = depth - 1 + ext

            # LMR: only for quiet, non-check moves.
            reduced = False
            if (
                depth >= 3
                and move_index >= 4
                and not is_capture
                and not gives_check
                and not in_check
                and move.promotion is None
            ):
                reduction = self._lmr_reduction(depth, move_index)
                if reduction > 0 and new_depth - reduction > 0:
                    reduced = True
                    score = -self._negamax(
                        board,
                        new_depth - reduction,
                        -alpha - 1,
                        -alpha,
                        ply=ply + 1,
                        allow_null=True,
                    )
                    # If it improves alpha, re-search at full depth/window.
                    if score > alpha:
                        score = -self._negamax(
                            board,
                            new_depth,
                            -beta,
                            -alpha,
                            ply=ply + 1,
                            allow_null=True,
                        )
                else:
                    reduction = 0

            if not reduced:
                # PVS: full window for first move, null window for the rest.
                if move_index == 0:
                    score = -self._negamax(board, new_depth, -beta, -alpha, ply=ply + 1, allow_null=True)
                else:
                    score = -self._negamax(board, new_depth, -alpha - 1, -alpha, ply=ply + 1, allow_null=True)
                    if score > alpha:
                        score = -self._negamax(board, new_depth, -beta, -alpha, ply=ply + 1, allow_null=True)

            self._pop_rep(board)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                # Beta cutoff => update killers/history
                if not is_capture and move.promotion is None:
                    self._store_killer(ply, move)
                    self._store_history(board.turn, move, depth)
                # Store TT as LOWER bound
                self._tt_store(key, depth, score, _TTFlag.LOWER, move, ply=ply)
                return beta

        # No cutoff: store TT (EXACT if improved, else UPPER)
        flag = _TTFlag.EXACT if best_score > original_alpha else _TTFlag.UPPER
        self._tt_store(key, depth, best_score, flag, best_move, ply=ply)

        return best_score

    # --------------------------
    # Quiescence search
    # --------------------------

    def _quiescence(self, board: chess.Board, alpha: int, beta: int, *, ply: int) -> int:
        # Periodic stop checks.
        if (self._nodes_searched & (self._STOP_CHECK_PERIOD - 1)) == 0:
            self._check_stop()

        self._nodes_searched += 1

        key = chess.polyglot.zobrist_hash(board)
        if self._rep_counts.get(key, 0) >= 3:
            return 0
        if board.is_fifty_moves():
            return 0

        if board.is_game_over():
            return int(self._heuristic.evaluate_result(board, ply))

        stand_pat = int(self._heuristic.evaluate_position(board))

        if stand_pat >= beta:
            return beta

        # Delta pruning: if even winning a queen can't raise alpha, stop (middle-game only).
        if len(board.piece_map()) > 8 and stand_pat + PieceValues.QUEEN_VALUE < alpha:
            return alpha

        if stand_pat > alpha:
            alpha = stand_pat

        for move in self._ordered_qmoves(board):
            # SEE-lite filter for captures that drop material.
            if board.is_capture(move) and not self._see_ge(board, move, threshold=0):
                continue

            board.push(move)
            self._push_rep(board)

            score = -self._quiescence(board, -beta, -alpha, ply=ply + 1)

            self._pop_rep(board)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def _ordered_qmoves(self, board: chess.Board) -> Iterator[chess.Move]:
        """Captures and checking moves for quiescence, ordered by MVV/LVA and promotions."""
        moves = [m for m in board.legal_moves if board.is_capture(m) or board.gives_check(m)]
        moves.sort(key=lambda m: self._qmove_order_key(board, m), reverse=True)
        return iter(moves)

    # --------------------------
    # Move ordering
    # --------------------------

    @staticmethod
    def _piece_value(piece_type: int | None) -> int:
        if piece_type is None:
            return 0
        return int(PieceValues.as_dict().get(piece_type, 0))

    def _move_order_key(self, board: chess.Board, move: chess.Move, tt_move: chess.Move | None, *, ply: int) -> int:
        # Big buckets: TT move, captures, killers, history.
        if tt_move is not None and move == tt_move:
            return 10_000_000

        if board.is_capture(move):
            victim_type = chess.PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
            attacker_type = board.piece_type_at(move.from_square)
            mvv_lva = self._piece_value(victim_type) * 10 - self._piece_value(attacker_type)
            promo = self._piece_value(move.promotion) * 5 if move.promotion else 0
            return 9_000_000 + mvv_lva + promo

        # Killer moves (quiet only)
        if ply < len(self._killers):
            k1, k2 = self._killers[ply]
            if k1 is not None and move == k1:
                return 8_500_000
            if k2 is not None and move == k2:
                return 8_400_000

        # History heuristic
        h = self._history_score(board.turn, move)
        return 1_000_000 + h

    def _qmove_order_key(self, board: chess.Board, move: chess.Move) -> int:
        score = 0
        if board.is_capture(move):
            victim_type = chess.PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
            attacker_type = board.piece_type_at(move.from_square)
            score += self._piece_value(victim_type) * 10 - self._piece_value(attacker_type)

        if move.promotion:
            score += self._piece_value(move.promotion) * 5

        if board.gives_check(move):
            score += 50

        return score

    # --------------------------
    # Killer / history helpers
    # --------------------------

    def _store_killer(self, ply: int, move: chess.Move) -> None:
        if ply >= len(self._killers):
            return
        k1, k2 = self._killers[ply]
        if k1 == move:
            return
        self._killers[ply][1] = k1
        self._killers[ply][0] = move

    def _history_index(self, color: bool, move: chess.Move) -> int:
        # 2 * 64 * 64 = 8192
        base = 4096 if color else 0
        return base + (move.from_square * 64 + move.to_square)

    def _store_history(self, color: bool, move: chess.Move, depth: int) -> None:
        idx = self._history_index(color, move)
        self._history[idx] += depth * depth

    def _history_score(self, color: bool, move: chess.Move) -> int:
        return self._history[self._history_index(color, move)]

    # --------------------------
    # LMR / null-move helpers
    # --------------------------

    @staticmethod
    def _lmr_reduction(depth: int, move_index: int) -> int:
        # Simple and conservative:
        # - reduce 1 for late moves in deeper nodes
        # - reduce 2 only when depth is large and move is very late
        if depth < 3 or move_index < 4:
            return 0
        if depth >= 6 and move_index >= 10:
            return 2
        return 1

    @staticmethod
    def _can_null_move(board: chess.Board) -> bool:
        """Guard against pawn-only zugzwangs: allow null if side to move has non-pawn material."""
        color = board.turn
        return any(
            board.pieces(pt, color)
            for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
        )

    # --------------------------
    # TT helpers
    # --------------------------

    @staticmethod
    def _tt_score_to_store(score: int, ply: int) -> int:
        mate = Constants.MATE_SCORE
        if score >= mate - 10_000:
            return score + ply
        if score <= -mate + 10_000:
            return score - ply
        return score

    @staticmethod
    def _tt_score_to_search(score: int, ply: int) -> int:
        mate = Constants.MATE_SCORE
        if score >= mate - 10_000:
            return score - ply
        if score <= -mate + 10_000:
            return score + ply
        return score

    def _tt_store(
        self,
        key: int,
        depth: int,
        score: int,
        flag: _TTFlag,
        best_move: chess.Move | None,
        *,
        ply: int,
    ) -> None:
        # Keep deeper entries from the same generation.
        existing = self._tt.get(key)
        if existing is not None and existing.generation == self._tt_generation and existing.depth > depth:
            return

        stored = _TTEntry(
            key=key,
            depth=depth,
            score=self._tt_score_to_store(int(score), ply=ply),
            flag=flag,
            best_move=best_move,
            generation=self._tt_generation,
        )
        self._tt[key] = stored

    # --------------------------
    # Repetition helpers
    # --------------------------

    def _push_rep(self, board: chess.Board) -> None:
        k = chess.polyglot.zobrist_hash(board)
        self._key_stack.append(k)
        self._rep_counts[k] = self._rep_counts.get(k, 0) + 1

    def _pop_rep(self, board: chess.Board) -> None:
        # board is already in the state we appended for, so pop last key
        k = self._key_stack.pop()
        c = self._rep_counts.get(k, 0) - 1
        if c <= 0:
            self._rep_counts.pop(k, None)
        else:
            self._rep_counts[k] = c

    # --------------------------
    # SEE-lite
    # --------------------------

    def _see_ge(self, board: chess.Board, move: chess.Move, *, threshold: int) -> bool:
        """A lightweight, conservative SEE approximation.

        Returns True if the capture is *likely* to win at least `threshold` centipawns.

        This is not a full SEE implementation (full SEE needs incremental sliding attacks).
        It still helps a lot for:
        - ordering (prefer clearly winning captures),
        - pruning obviously losing captures in deeper nodes/quiescence.
        """
        if not board.is_capture(move):
            return True

        us = board.turn
        to_sq = move.to_square

        victim_type = chess.PAWN if board.is_en_passant(move) else board.piece_type_at(to_sq)
        attacker_type = board.piece_type_at(move.from_square)

        victim_val = self._piece_value(victim_type)
        attacker_val = self._piece_value(attacker_type)

        # Promotions are usually tactically forcing; treat them as "good enough" for SEE purposes.
        if move.promotion is not None:
            return True

        # Immediate material delta.
        net = victim_val - attacker_val

        # If it is already above threshold, accept.
        if net >= threshold:
            return True

        # If the square is not defended by the opponent in the current position, treat as safe.
        # (Approximation: ignores discovered attacks by moving the attacker away.)
        if not board.attackers(not us, to_sq):
            return True

        # Otherwise, assume recapture happens => net is the best approximation we can do cheaply.
        return net >= threshold

    # --------------------------
    # PV extraction helper
    # --------------------------

    def _extract_pv(self, board: chess.Board, first_move: chess.Move, depth: int) -> list[chess.Move]:
        """Extract a PV by following TT best moves from the current position (non-destructive)."""
        pv: list[chess.Move] = []
        b = board.copy(stack=False)
        b.push(first_move)

        seen: set[int] = set()
        for _ in range(max(depth - 1, 0)):
            k = chess.polyglot.zobrist_hash(b)
            if k in seen:
                break
            seen.add(k)

            entry = self._tt.get(k)
            if not entry or not entry.best_move:
                break
            mv = entry.best_move
            if mv not in b.legal_moves:
                break
            pv.append(mv)
            b.push(mv)

        return pv