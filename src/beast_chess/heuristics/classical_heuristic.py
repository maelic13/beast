"""Classical (hand-crafted) evaluation.

This implementation replaces the original square-by-square loops with
bitboard-based iteration and precomputed tables to make evaluation much faster.

Implemented techniques (incl. the 5 upgrades requested):
1) Tapered evaluation (middlegame/endgame interpolation)
2) King safety: pawn shield + (half-)open files near the king
3) Passed pawns: rank bonus + king distance + rook-behind-passed-pawn bonus
4) Endgame scaling: encourage queen trades when ahead (advantage grows when queens are off)
5) Tempo bonus (side-to-move)

All scores are in centipawns and the final score is returned from the
*side-to-move* perspective (positive = good for side to move).
"""

from __future__ import annotations

import chess

from .infra import Heuristic, PieceValues

# ---------------------------------------------------------------------------
# Bitboard helpers (fast iteration)
# ---------------------------------------------------------------------------


def _iter_squares(bb: int):
    """Iterate squares (0..63) from a bitboard."""
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        yield sq
        bb &= bb - 1


# File masks (a..h) and rank masks (1..8)
_FILE_MASKS = []
_RANK_MASKS = []
for file_idx in range(8):
    mask = 0
    for rank in range(8):
        sq = chess.square(file_idx, rank)
        mask |= 1 << sq
    _FILE_MASKS.append(mask)

for rank_idx in range(8):
    mask = 0
    for file in range(8):
        sq = chess.square(file, rank_idx)
        mask |= 1 << sq
    _RANK_MASKS.append(mask)

# Passed pawn masks: squares in front of a pawn on same/adjacent files.
# Index: PASSED_MASK[color_index][square]
_PASSED_MASK = [[0] * 64 for _ in range(2)]
for sq in range(64):
    f = chess.square_file(sq)
    r = chess.square_rank(sq)

    # White: squares with higher ranks
    w_mask = 0
    for df in (-1, 0, 1):
        nf = f + df
        if 0 <= nf < 8:
            for nr in range(r + 1, 8):
                w_mask |= 1 << chess.square(nf, nr)
    _PASSED_MASK[0][sq] = w_mask

    # Black: squares with lower ranks
    b_mask = 0
    for df in (-1, 0, 1):
        nf = f + df
        if 0 <= nf < 8:
            for nr in range(r - 1, -1, -1):
                b_mask |= 1 << chess.square(nf, nr)
    _PASSED_MASK[1][sq] = b_mask


# ---------------------------------------------------------------------------
# Piece-square tables
#
# These are intentionally small/smooth (good enough for a simple engine).
# Values are in centipawns.
# ---------------------------------------------------------------------------

# Base PSTs are written for White, from a1(0) .. h8(63).
# For Black pieces, we use chess.square_mirror().

_PST_MG = {
    chess.PAWN: (
         0,  0,  0,  0,  0,  0,  0,  0,
         5, 10, 10,-10,-10, 10, 10,  5,
         5, -5,-10,  0,  0,-10, -5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5,  5, 10, 25, 25, 10,  5,  5,
        10, 10, 20, 30, 30, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
         0,  0,  0,  0,  0,  0,  0,  0,
    ),
    chess.KNIGHT: (
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ),
    chess.BISHOP: (
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ),
    chess.ROOK: (
          0,  0,  5, 10, 10,  5,  0,  0,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
          5, 10, 10, 10, 10, 10, 10,  5,
          0,  0,  0,  0,  0,  0,  0,  0,
    ),
    chess.QUEEN: (
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20,
    ),
    chess.KING: (
        20, 30, 10,  0,  0, 10, 30, 20,
        20, 20,  0,  0,  0,  0, 20, 20,
       -10,-20,-20,-20,-20,-20,-20,-10,
       -20,-30,-30,-40,-40,-30,-30,-20,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
    ),
}

_PST_EG = {
    chess.PAWN: (
         0,  0,  0,  0,  0,  0,  0,  0,
        10, 10, 10, 10, 10, 10, 10, 10,
        20, 20, 20, 25, 25, 20, 20, 20,
        30, 30, 30, 35, 35, 30, 30, 30,
        40, 40, 40, 45, 45, 40, 40, 40,
        60, 60, 60, 70, 70, 60, 60, 60,
        90, 90, 90,100,100, 90, 90, 90,
         0,  0,  0,  0,  0,  0,  0,  0,
    ),
    chess.KNIGHT: (
        -40,-30,-20,-20,-20,-20,-30,-40,
        -30,-10,  0,  0,  0,  0,-10,-30,
        -20,  0, 10, 15, 15, 10,  0,-20,
        -20,  5, 15, 20, 20, 15,  5,-20,
        -20,  0, 15, 20, 20, 15,  0,-20,
        -20,  5, 10, 15, 15, 10,  5,-20,
        -30,-10,  0,  5,  5,  0,-10,-30,
        -40,-30,-20,-20,-20,-20,-30,-40,
    ),
    chess.BISHOP: (
        -10, -5, -5, -5, -5, -5, -5,-10,
         -5,  5,  0,  0,  0,  0,  5, -5,
         -5, 10, 10, 10, 10, 10, 10, -5,
         -5,  0, 10, 10, 10, 10,  0, -5,
         -5,  5,  5, 10, 10,  5,  5, -5,
         -5,  0,  5, 10, 10,  5,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
        -10, -5, -5, -5, -5, -5, -5,-10,
    ),
    chess.ROOK: _PST_MG[chess.ROOK],
    chess.QUEEN: _PST_MG[chess.QUEEN],
    chess.KING: (
       -50,-30,-30,-30,-30,-30,-30,-50,
       -30,-30,  0,  0,  0,  0,-30,-30,
       -30,-10, 20, 30, 30, 20,-10,-30,
       -30,-10, 30, 40, 40, 30,-10,-30,
       -30,-10, 30, 40, 40, 30,-10,-30,
       -30,-10, 20, 30, 30, 20,-10,-30,
       -30,-20,-10,  0,  0,-10,-20,-30,
       -50,-40,-30,-20,-20,-30,-40,-50,
    ),
}


# ---------------------------------------------------------------------------
# Evaluation weights (centipawns)
# ---------------------------------------------------------------------------

_MAX_PHASE = 24

# Game phase weights per piece type (common convention)
_PHASE_N = 1
_PHASE_B = 1
_PHASE_R = 2
_PHASE_Q = 4

# King safety (MG)
_KS_SHIELD_PAWN = 12        # per pawn in the king shield
_KS_MISSING_PAWN = 18       # penalty per missing shield pawn
_KS_HALFOPEN_FILE = 12      # penalty per half-open file near king
_KS_OPEN_FILE = 22          # penalty per fully open file near king (no pawns at all)

# Passed pawns (EG)
_PASSED_BONUS_BY_ADVANCE = (0, 10, 20, 35, 55, 80, 110)  # 0..6
_ROOK_BEHIND_PASSED = 25
_KING_DISTANCE_PASSED = 6   # per (distance delta)

# Queen trade scaling (EG)
_QUEEN_TRADE_SCALE_NUM = 20  # advantage/20 = +5% scaling if queens are off

# Tempo
_TEMPO_MG = 10
_TEMPO_EG = 5


class ClassicalHeuristic(Heuristic):
    @staticmethod
    def use_quiescence() -> bool:
        return True

    def _evaluate_internal(self, board: chess.Board) -> float:
        # Piece bitboards by color
        occ_w = board.occupied_co[chess.WHITE]
        occ_b = board.occupied_co[chess.BLACK]

        wp = board.pawns & occ_w
        bp = board.pawns & occ_b
        wn = board.knights & occ_w
        bn = board.knights & occ_b
        wb = board.bishops & occ_w
        bb = board.bishops & occ_b
        wr = board.rooks & occ_w
        br = board.rooks & occ_b
        wq = board.queens & occ_w
        bq = board.queens & occ_b
        wk_bb = board.kings & occ_w
        bk_bb = board.kings & occ_b

        # Material (white - black)
        pv = PieceValues
        mat = (
            wp.bit_count() * pv.PAWN_VALUE
            + wn.bit_count() * pv.KNIGHT_VALUE
            + wb.bit_count() * pv.BISHOP_VALUE
            + wr.bit_count() * pv.ROOK_VALUE
            + wq.bit_count() * pv.QUEEN_VALUE
            - bp.bit_count() * pv.PAWN_VALUE
            - bn.bit_count() * pv.KNIGHT_VALUE
            - bb.bit_count() * pv.BISHOP_VALUE
            - br.bit_count() * pv.ROOK_VALUE
            - bq.bit_count() * pv.QUEEN_VALUE
        )

        # Game phase (0..24)
        phase = (
            (wn.bit_count() + bn.bit_count()) * _PHASE_N
            + (wb.bit_count() + bb.bit_count()) * _PHASE_B
            + (wr.bit_count() + br.bit_count()) * _PHASE_R
            + (wq.bit_count() + bq.bit_count()) * _PHASE_Q
        )
        if phase > _MAX_PHASE:
            phase = _MAX_PHASE

        mg = mat
        eg = mat

        # PST contribution
        mg += self._pst_score(wp, wn, wb, wr, wq, wk_bb, bp, bn, bb, br, bq, bk_bb, _PST_MG)
        eg += self._pst_score(wp, wn, wb, wr, wq, wk_bb, bp, bn, bb, br, bq, bk_bb, _PST_EG)

        # Tempo bonus (white-to-move perspective)
        tempo_sign = 1 if board.turn == chess.WHITE else -1
        mg += tempo_sign * _TEMPO_MG
        eg += tempo_sign * _TEMPO_EG

        # King safety (mostly MG; scale by presence of queens)
        q_count = wq.bit_count() + bq.bit_count()
        if q_count:
            ks_factor_num = 2 if q_count >= 2 else 1  # 2 => full, 1 => half
            ks = (self._king_safety(board, chess.WHITE, wp, bp) - self._king_safety(board, chess.BLACK, bp, wp))
            mg += (ks * ks_factor_num) // 2

        # Passed pawns / endgame play
        eg += self._passed_pawn_score(board, chess.WHITE, wp, bp, wr, br)
        eg -= self._passed_pawn_score(board, chess.BLACK, bp, wp, br, wr)

        # Queen trade scaling: when queens are off, a material edge tends to convert easier.
        if q_count == 0 and mat != 0:
            eg += mat // _QUEEN_TRADE_SCALE_NUM

        # Tapered final (white perspective)
        score_white = (mg * phase + eg * (_MAX_PHASE - phase)) // _MAX_PHASE

        # Return from side-to-move perspective
        return float(score_white if board.turn == chess.WHITE else -score_white)

    @staticmethod
    def _pst_score(
        wp: int, wn: int, wb: int, wr: int, wq: int, wk: int,
        bp: int, bn: int, bb: int, br: int, bq: int, bk: int,
        pst: dict[int, tuple[int, ...]],
    ) -> int:
        score = 0

        for sq in _iter_squares(wp):
            score += pst[chess.PAWN][sq]
        for sq in _iter_squares(wn):
            score += pst[chess.KNIGHT][sq]
        for sq in _iter_squares(wb):
            score += pst[chess.BISHOP][sq]
        for sq in _iter_squares(wr):
            score += pst[chess.ROOK][sq]
        for sq in _iter_squares(wq):
            score += pst[chess.QUEEN][sq]
        for sq in _iter_squares(wk):
            score += pst[chess.KING][sq]

        for sq in _iter_squares(bp):
            score -= pst[chess.PAWN][chess.square_mirror(sq)]
        for sq in _iter_squares(bn):
            score -= pst[chess.KNIGHT][chess.square_mirror(sq)]
        for sq in _iter_squares(bb):
            score -= pst[chess.BISHOP][chess.square_mirror(sq)]
        for sq in _iter_squares(br):
            score -= pst[chess.ROOK][chess.square_mirror(sq)]
        for sq in _iter_squares(bq):
            score -= pst[chess.QUEEN][chess.square_mirror(sq)]
        for sq in _iter_squares(bk):
            score -= pst[chess.KING][chess.square_mirror(sq)]

        return score

    @staticmethod
    def _king_safety(board: chess.Board, color: chess.Color, own_pawns: int, opp_pawns: int) -> int:
        # If king missing (should not happen), ignore.
        ksq = board.king(color)
        if ksq is None:
            return 0

        f = chess.square_file(ksq)
        r = chess.square_rank(ksq)

        # Determine shield squares: 1 and 2 ranks in front of king, on files (f-1,f,f+1)
        score = 0
        forward = 1 if color == chess.WHITE else -1

        shield_squares = []
        for df in (-1, 0, 1):
            nf = f + df
            if 0 <= nf < 8:
                r1 = r + forward
                r2 = r + 2 * forward
                if 0 <= r1 < 8:
                    shield_squares.append(chess.square(nf, r1))
                if 0 <= r2 < 8:
                    shield_squares.append(chess.square(nf, r2))

        shield_mask = 0
        for sq in shield_squares:
            shield_mask |= 1 << sq

        pawns_in_shield = (own_pawns & shield_mask).bit_count()
        missing = len(shield_squares) - pawns_in_shield

        score += pawns_in_shield * _KS_SHIELD_PAWN
        score -= missing * _KS_MISSING_PAWN

        # (Half-)open files near king (king file and adjacent files)
        for df in (-1, 0, 1):
            nf = f + df
            if 0 <= nf < 8:
                fm = _FILE_MASKS[nf]
                own_on_file = own_pawns & fm
                any_on_file = (own_pawns | opp_pawns) & fm
                if own_on_file == 0:
                    # half-open file against the king
                    score -= _KS_HALFOPEN_FILE
                    if any_on_file == 0:
                        score -= (_KS_OPEN_FILE - _KS_HALFOPEN_FILE)

        return score

    @staticmethod
    def _passed_pawn_score(
        board: chess.Board,
        color: chess.Color,
        own_pawns: int,
        opp_pawns: int,
        own_rooks: int,
        opp_rooks: int,
    ) -> int:
        """Endgame score contribution for passed pawns of `color` (returned from that color's POV)."""
        score = 0
        idx = 0 if color == chess.WHITE else 1

        k_own = board.king(color)
        k_opp = board.king(not color)
        if k_own is None or k_opp is None:
            return 0

        for sq in _iter_squares(own_pawns):
            # Passed pawn test
            if opp_pawns & _PASSED_MASK[idx][sq]:
                continue

            rank = chess.square_rank(sq)
            advance = (rank - 1) if color == chess.WHITE else (6 - rank)
            if advance < 0:
                advance = 0
            if advance > 6:
                advance = 6

            score += _PASSED_BONUS_BY_ADVANCE[advance]

            # Rook behind passed pawn
            file_idx = chess.square_file(sq)
            file_mask = _FILE_MASKS[file_idx]
            rooks_on_file = own_rooks & file_mask
            if rooks_on_file:
                pawn_rank = rank
                for rsq in _iter_squares(rooks_on_file):
                    rr = chess.square_rank(rsq)
                    if (color == chess.WHITE and rr < pawn_rank) or (color == chess.BLACK and rr > pawn_rank):
                        score += _ROOK_BEHIND_PASSED
                        break

            # King distance: own king wants to support, opponent king wants to stop
            # Use Manhattan distance (fast and good enough).
            dist_own = abs(chess.square_file(k_own) - chess.square_file(sq)) + abs(chess.square_rank(k_own) - rank)
            dist_opp = abs(chess.square_file(k_opp) - chess.square_file(sq)) + abs(chess.square_rank(k_opp) - rank)
            score += (dist_opp - dist_own) * _KING_DISTANCE_PASSED

        return score
