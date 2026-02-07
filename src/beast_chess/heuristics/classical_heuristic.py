"""Classical (hand-tuned) evaluation.

This file originally implemented a very compact, mostly piece-count + piece-distance style
heuristic. This rewrite keeps the public API intact, but:

* fixes a couple of correctness bugs (see analysis in the assistant message), and
* replaces the hot-path evaluation with a faster tapered (midgame/endgame) eval based on
  bitboards + precomputed tables.

No extra dependencies are introduced (still only python-chess).
"""

from __future__ import annotations

from dataclasses import dataclass

import chess
from chess import (
    BISHOP,
    BLACK,
    KNIGHT,
    PAWN,
    QUEEN,
    ROOK,
    WHITE,
    Board,
)

from .infra import Heuristic, PieceValues

# ---------------------------------------------------------------------------
# Precomputed helpers (module-load time, not per-eval)
# ---------------------------------------------------------------------------

BB_ALL = chess.BB_ALL  # 0xffff_ffff_ffff_ffff in python-chess 1.11.x

# Vertical mirror a1<->a8 etc.
MIRROR: list[int] = [sq ^ 56 for sq in range(64)]

# File masks: FILE_MASKS[file] where file is 0..7.
FILE_MASKS: list[int] = []
for f in range(8):
    mask = 0
    for r in range(8):
        mask |= 1 << (r * 8 + f)
    FILE_MASKS.append(mask)

# Adjacent files mask for isolated pawn detection.
ADJ_FILE_MASKS: list[int] = []
for f in range(8):
    mask = 0
    if f - 1 >= 0:
        mask |= FILE_MASKS[f - 1]
    if f + 1 <= 7:
        mask |= FILE_MASKS[f + 1]
    ADJ_FILE_MASKS.append(mask)

# Passed pawn masks: squares "in front" on same/adjacent files.
PASSED_MASK_WHITE: list[int] = [0] * 64
PASSED_MASK_BLACK: list[int] = [0] * 64
for sq in range(64):
    r = sq >> 3
    f = sq & 7

    # White pawns move towards increasing ranks.
    mask_w = 0
    for rr in range(r + 1, 8):
        for ff in (f - 1, f, f + 1):
            if 0 <= ff <= 7:
                mask_w |= 1 << (rr * 8 + ff)
    PASSED_MASK_WHITE[sq] = mask_w

    # Black pawns move towards decreasing ranks.
    mask_b = 0
    for rr in range(r - 1, -1, -1):
        for ff in (f - 1, f, f + 1):
            if 0 <= ff <= 7:
                mask_b |= 1 << (rr * 8 + ff)
    PASSED_MASK_BLACK[sq] = mask_b


def _center_score(sq: int) -> int:
    """0..6, higher means closer to center (cheap integer metric)."""
    f = sq & 7
    r = sq >> 3
    return min(f, 7 - f) + min(r, 7 - r)


def _gen_pst() -> tuple[dict[int, list[int]], dict[int, list[int]]]:
    """Generate simple piece-square tables.

    Tables are from White's point of view (Black uses MIRROR[sq]).

    This is intentionally lightweight: we rely on extra terms (pawn structure, mobility,
    rook files, bishop pair) for strength.
    """
    mg: dict[int, list[int]] = {PAWN: [0] * 64, KNIGHT: [0] * 64, BISHOP: [0] * 64, ROOK: [0] * 64, QUEEN: [0] * 64, chess.KING: [0] * 64}
    eg: dict[int, list[int]] = {PAWN: [0] * 64, KNIGHT: [0] * 64, BISHOP: [0] * 64, ROOK: [0] * 64, QUEEN: [0] * 64, chess.KING: [0] * 64}

    # Small hand-tuned constants.
    for sq in range(64):
        r = sq >> 3
        f = sq & 7
        c = _center_score(sq)  # 0..6

        # Pawn: encourage advancing + central files.
        # Starting rank is r=1.
        pawn_adv = max(0, r - 1)
        pawn_file = (min(f, 7 - f) - 1) * 2  # center files positive, edge files negative
        mg[PAWN][sq] = pawn_adv * 10 + pawn_file
        eg[PAWN][sq] = pawn_adv * 14 + pawn_file

        # Knight: strongly prefer center.
        mg[KNIGHT][sq] = c * 6
        eg[KNIGHT][sq] = c * 4

        # Bishop: prefer center, but less than knights.
        mg[BISHOP][sq] = c * 4
        eg[BISHOP][sq] = c * 3

        # Rook: prefer 7th rank a bit.
        mg[ROOK][sq] = (15 if r == 6 else 0)
        eg[ROOK][sq] = (10 if r == 6 else 0)

        # Queen: mild centralization.
        mg[QUEEN][sq] = c * 2
        eg[QUEEN][sq] = c * 1

        # King: avoid center in middlegame, seek center in endgame.
        mg[chess.KING][sq] = -c * 10
        eg[chess.KING][sq] = c * 12

    # Extra castling-square preference in middlegame.
    for sq in (chess.G1, chess.C1):
        mg[chess.KING][sq] += 20
    return mg, eg


MG_PST, EG_PST = _gen_pst()

# Phase weights for tapered eval.
PHASE_VALUE = {KNIGHT: 1, BISHOP: 1, ROOK: 2, QUEEN: 4}
MAX_PHASE = 24


@dataclass(frozen=True, slots=True)
class _EvalWeights:
    # Pawn structure.
    doubled_mg: int = 14
    doubled_eg: int = 10
    isolated_mg: int = 12
    isolated_eg: int = 10
    passed_mg_base: int = 8
    passed_eg_base: int = 16

    # Mobility (middlegame only, mostly).
    mob_n: int = 4
    mob_b: int = 4
    mob_r: int = 2
    mob_q: int = 1

    # Bishop pair.
    bishop_pair_mg: int = 25
    bishop_pair_eg: int = 35

    # Rook activity.
    rook_open_file_mg: int = 18
    rook_open_file_eg: int = 10
    rook_semi_open_file_mg: int = 9
    rook_semi_open_file_eg: int = 6
    rook_7th_mg: int = 15
    rook_7th_eg: int = 10


W = _EvalWeights()


class ClassicalHeuristic(Heuristic):
    """Classical evaluation (fast tapered eval)."""

    @staticmethod
    def use_quiescence() -> bool:
        return True

    def _evaluate_internal(self, board: Board) -> float:
        # --- Bitboards per color (cheap) ---
        occ_w = board.occupied_co[WHITE]
        occ_b = board.occupied_co[BLACK]

        pawns_w = board.pawns & occ_w
        pawns_b = board.pawns & occ_b
        knights_w = board.knights & occ_w
        knights_b = board.knights & occ_b
        bishops_w = board.bishops & occ_w
        bishops_b = board.bishops & occ_b
        rooks_w = board.rooks & occ_w
        rooks_b = board.rooks & occ_b
        queens_w = board.queens & occ_w
        queens_b = board.queens & occ_b
        kings_w = board.kings & occ_w
        kings_b = board.kings & occ_b

        # --- Material values (from your PieceValues) ---
        pawn_v = int(PieceValues.PAWN_VALUE)
        knight_v = int(PieceValues.KNIGHT_VALUE)
        bishop_v = int(PieceValues.BISHOP_VALUE)
        rook_v = int(PieceValues.ROOK_VALUE)
        queen_v = int(PieceValues.QUEEN_VALUE)

        # --- Tapered evaluation accumulators ---
        mg = 0
        eg = 0

        # Phase: the more non-pawn material on board, the more "middlegame".
        phase = 0
        phase += PHASE_VALUE[KNIGHT] * int((knights_w | knights_b).bit_count())
        phase += PHASE_VALUE[BISHOP] * int((bishops_w | bishops_b).bit_count())
        phase += PHASE_VALUE[ROOK] * int((rooks_w | rooks_b).bit_count())
        phase += PHASE_VALUE[QUEEN] * int((queens_w | queens_b).bit_count())
        if phase > MAX_PHASE:
            phase = MAX_PHASE

        # --- Piece iteration (tight loops, bit scanning) ---
        def add_piece_squares(bb: int, piece_type: int, base_value: int, sign: int) -> None:
            nonlocal mg, eg
            pst_mg = MG_PST[piece_type]
            pst_eg = EG_PST[piece_type]
            if sign > 0:
                while bb:
                    lsb = bb & -bb
                    sq = lsb.bit_length() - 1
                    mg += base_value + pst_mg[sq]
                    eg += base_value + pst_eg[sq]
                    bb ^= lsb
            else:
                while bb:
                    lsb = bb & -bb
                    sq = lsb.bit_length() - 1
                    msq = MIRROR[sq]
                    mg -= base_value + pst_mg[msq]
                    eg -= base_value + pst_eg[msq]
                    bb ^= lsb

        add_piece_squares(pawns_w, PAWN, pawn_v, +1)
        add_piece_squares(pawns_b, PAWN, pawn_v, -1)
        add_piece_squares(knights_w, KNIGHT, knight_v, +1)
        add_piece_squares(knights_b, KNIGHT, knight_v, -1)
        add_piece_squares(bishops_w, BISHOP, bishop_v, +1)
        add_piece_squares(bishops_b, BISHOP, bishop_v, -1)
        add_piece_squares(rooks_w, ROOK, rook_v, +1)
        add_piece_squares(rooks_b, ROOK, rook_v, -1)
        add_piece_squares(queens_w, QUEEN, queen_v, +1)
        add_piece_squares(queens_b, QUEEN, queen_v, -1)

        # Kings: base value is not added; only PST.
        add_piece_squares(kings_w, chess.KING, 0, +1)
        add_piece_squares(kings_b, chess.KING, 0, -1)

        # -------------------------------------------------------------------
        # 1) Pawn structure: doubled, isolated, passed
        # -------------------------------------------------------------------
        all_pawns = pawns_w | pawns_b

        # Doubled pawns: count per file.
        for f in range(8):
            fm = FILE_MASKS[f]
            cw = int((pawns_w & fm).bit_count())
            cb = int((pawns_b & fm).bit_count())
            if cw > 1:
                mg -= (cw - 1) * W.doubled_mg
                eg -= (cw - 1) * W.doubled_eg
            if cb > 1:
                mg += (cb - 1) * W.doubled_mg
                eg += (cb - 1) * W.doubled_eg

        # Isolated and passed pawns need per-pawn checks (<=8 each side).
        bb = pawns_w
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            f = sq & 7
            r = sq >> 3

            if (pawns_w & ADJ_FILE_MASKS[f]) == 0:
                mg -= W.isolated_mg
                eg -= W.isolated_eg

            if (pawns_b & PASSED_MASK_WHITE[sq]) == 0:
                adv = max(0, r - 1)  # 0..5
                mg += W.passed_mg_base * adv
                eg += W.passed_eg_base * adv

            bb ^= lsb

        bb = pawns_b
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            f = sq & 7
            r = sq >> 3

            if (pawns_b & ADJ_FILE_MASKS[f]) == 0:
                mg += W.isolated_mg
                eg += W.isolated_eg

            if (pawns_w & PASSED_MASK_BLACK[sq]) == 0:
                adv = max(0, 6 - r)  # 0..5
                mg -= W.passed_mg_base * adv
                eg -= W.passed_eg_base * adv

            bb ^= lsb

        # -------------------------------------------------------------------
        # 2) Mobility (piece activity)
        # -------------------------------------------------------------------
        free_w = BB_ALL ^ occ_w
        free_b = BB_ALL ^ occ_b

        def mobility(bb: int, weight: int, free: int, sign: int) -> None:
            nonlocal mg
            while bb:
                lsb = bb & -bb
                sq = lsb.bit_length() - 1
                att = int(board.attacks(sq)) & free
                mg += sign * weight * int(att.bit_count())
                bb ^= lsb

        mobility(knights_w, W.mob_n, free_w, +1)
        mobility(knights_b, W.mob_n, free_b, -1)
        mobility(bishops_w, W.mob_b, free_w, +1)
        mobility(bishops_b, W.mob_b, free_b, -1)
        mobility(rooks_w, W.mob_r, free_w, +1)
        mobility(rooks_b, W.mob_r, free_b, -1)
        mobility(queens_w, W.mob_q, free_w, +1)
        mobility(queens_b, W.mob_q, free_b, -1)

        # -------------------------------------------------------------------
        # 3) Bishop pair
        # -------------------------------------------------------------------
        if int(bishops_w.bit_count()) >= 2:
            mg += W.bishop_pair_mg
            eg += W.bishop_pair_eg
        if int(bishops_b.bit_count()) >= 2:
            mg -= W.bishop_pair_mg
            eg -= W.bishop_pair_eg

        # -------------------------------------------------------------------
        # 4) Rooks on open/semi-open files + 7th rank
        # -------------------------------------------------------------------
        def rook_activity(rooks: int, own_pawns: int, sign: int) -> None:
            nonlocal mg, eg
            bb = rooks
            while bb:
                lsb = bb & -bb
                sq = lsb.bit_length() - 1
                f = sq & 7
                r = sq >> 3
                fm = FILE_MASKS[f]

                if (all_pawns & fm) == 0:
                    mg += sign * W.rook_open_file_mg
                    eg += sign * W.rook_open_file_eg
                elif (own_pawns & fm) == 0:
                    mg += sign * W.rook_semi_open_file_mg
                    eg += sign * W.rook_semi_open_file_eg

                # 7th rank pressure.
                if sign > 0 and r == 6:
                    mg += W.rook_7th_mg
                    eg += W.rook_7th_eg
                elif sign < 0 and r == 1:
                    mg -= W.rook_7th_mg
                    eg -= W.rook_7th_eg

                bb ^= lsb

        rook_activity(rooks_w, pawns_w, +1)
        rook_activity(rooks_b, pawns_b, -1)

        # -------------------------------------------------------------------
        # Blend MG/EG -> single score.
        # -------------------------------------------------------------------
        score = (mg * phase + eg * (MAX_PHASE - phase)) // MAX_PHASE

        # Return from POV of side to move (engine is using negamax).
        return float(score if board.turn == WHITE else -score)
