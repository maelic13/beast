# ruff: noqa: SLF001
from beast_chess.board import BISHOP, BLACK, KNIGHT, PAWN, QUEEN, ROOK, WHITE, Board
from beast_chess.board.attacks import (
    KING_ATTACKS,
    KNIGHT_ATTACKS,
    PAWN_ATTACKS,
    bishop_attacks,
    queen_attacks,
    rook_attacks,
)

from .infra import Heuristic

# ---------------------------------------------------------------------------
# Piece-square tables: well-known tuned values used across many open-source
# engines (PeSTO / Stockfish-derived, public domain chess programming knowledge).
# Indexed 0=a1 ... 63=h8 from White's perspective.
# For Black: use table[sq ^ 56].
# ---------------------------------------------------------------------------

# fmt: off

# -- Material values (middlegame / endgame) --
MG_PAWN_VAL = 82
EG_PAWN_VAL = 94
MG_KNIGHT_VAL = 337
EG_KNIGHT_VAL = 281
MG_BISHOP_VAL = 365
EG_BISHOP_VAL = 297
MG_ROOK_VAL = 477
EG_ROOK_VAL = 512
MG_QUEEN_VAL = 1025
EG_QUEEN_VAL = 936

# Phase weights for tapered eval (total phase = 24)
PHASE_KNIGHT = 1
PHASE_BISHOP = 1
PHASE_ROOK = 2
PHASE_QUEEN = 4
TOTAL_PHASE = 24

# -- Piece-square tables (White perspective, a1=index 0) --
# Rows: rank 1 (indices 0-7) through rank 8 (indices 56-63)

MG_PAWN_TABLE = (
      0, 0, 0, 0, 0, 0, 0, 0,  # rank 1
    -35, -1, -20, -23, -15, 24, 38, -22,  # rank 2
    -26, -4, -4, -10, 3, 3, 33, -12,  # rank 3
    -27, -2, -5, 12, 17, 6, 10, -25,  # rank 4
    -14, 13, 6, 21, 23, 12, 17, -23,  # rank 5
     -6, 7, 26, 31, 65, 56, 25, -20,  # rank 6
     98, 134, 61, 95, 68, 126, 34, -11,  # rank 7
      0, 0, 0, 0, 0, 0, 0, 0,  # rank 8
)

EG_PAWN_TABLE = (
      0, 0, 0, 0, 0, 0, 0, 0,
    -10, -6, 10, 0, 14, 7, -5, -19,
     -8, -4, 7, 22, 17, 16, 3, -14,
     13, 0, -13, 1, -1, -16, 3, -6,
     32, 24, 13, 5, -2, 4, 17, 17,
     56, 35, 41, 22, 26, 51, 56, 20,
    134, 108, 109, 107, 105, 104, 112, 108,
      0, 0, 0, 0, 0, 0, 0, 0,
)

MG_KNIGHT_TABLE = (
   -167, -89, -34, -49, 61, -97, -15, -107,
    -73, -41, 72, 36, 23, 62, 7, -17,
    -47, 60, 37, 65, 84, 129, 73, 44,
     -9, 17, 19, 53, 37, 69, 18, 22,
    -13, 4, 16, 13, 28, 19, 21, -8,
    -23, -9, 12, 10, 19, 17, 25, -16,
    -29, -53, -12, -3, -1, 18, -14, -19,
   -105, -21, -58, -33, -17, -28, -19, -23,
)

EG_KNIGHT_TABLE = (
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25, -8, -25, -2, -9, -25, -24, -52,
    -24, -20, 10, 9, -1, -9, -19, -41,
    -17, 3, 22, 22, 22, 11, 8, -18,
    -18, -6, 16, 25, 16, 17, 4, -18,
    -23, -3, -1, 15, 10, -3, -20, -22,
    -42, -20, -10, -5, -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
)

MG_BISHOP_TABLE = (
    -29, 4, -82, -37, -25, -42, 7, -8,
    -26, 16, -18, -13, 30, 59, 18, -47,
    -16, 37, 43, 40, 35, 50, 37, -2,
     -4, 5, 19, 50, 37, 37, 7, -2,
     -6, 13, 13, 26, 34, 12, 10, 4,
      0, 15, 15, 15, 14, 27, 18, 10,
      4, 15, 16, 0, 7, 21, 33, 1,
    -33, -3, -14, -21, -13, -12, -39, -21,
)

EG_BISHOP_TABLE = (
    -14, -21, -11, -8, -7, -9, -17, -24,
     -8, -4, 7, -12, -3, -13, -4, -14,
      2, -8, 0, -1, -2, 6, 0, 4,
     -3, 9, 12, 9, 14, 10, 3, 2,
     -6, 3, 13, 19, 7, 10, -3, -9,
    -12, -3, 8, 10, 13, 3, -7, -15,
    -14, -18, -7, -1, 4, -9, -15, -27,
    -23, -9, -23, -5, -9, -16, -5, -17,
)

MG_ROOK_TABLE = (
    -19, -13, 1, 17, 16, 7, -37, -26,
    -44, -16, -20, -9, -1, 11, -6, -71,
    -45, -25, -16, -17, 3, 0, -5, -33,
    -36, -26, -12, -1, 9, -7, 6, -23,
    -24, -11, 7, 26, 24, 35, -8, -20,
     -5, 19, 26, 36, 17, 45, 61, 16,
     27, 32, 58, 62, 80, 67, 26, 44,
     32, 42, 32, 51, 63, 9, 31, 43,
)

EG_ROOK_TABLE = (
    -9, 2, 3, -1, -5, -13, 4, -20,
    -6, -6, 0, 2, -9, -9, -11, -3,
    -4, 0, -5, -1, -7, -12, -8, -16,
     3, 5, 8, 4, -5, -6, -8, -11,
     4, 3, 13, 1, 2, 1, -1, 2,
     7, 7, 7, 5, 4, -3, -5, -3,
    11, 13, 13, 11, -3, 3, 8, 3,
    13, 10, 18, 15, 12, 12, 8, 5,
)

MG_QUEEN_TABLE = (
    -28, 0, 29, 12, 59, 44, 43, 45,
    -24, -39, -5, 1, -16, 57, 28, 54,
    -13, -17, 7, 8, 29, 56, 47, 57,
    -27, -27, -16, -16, -1, 17, -2, 1,
     -9, -26, -9, -10, -2, -4, 3, -3,
    -14, 2, -11, -2, -5, 2, 14, 5,
    -35, -8, 11, 2, 8, 15, -3, 1,
     -1, -18, -9, 10, -15, -25, -31, -50,
)

EG_QUEEN_TABLE = (
    -9, 22, 22, 27, 27, 19, 10, 20,
   -17, 20, 32, 41, 58, 25, 30, 0,
   -20, 6, 9, 49, 47, 35, 19, 9,
     3, 22, 24, 45, 57, 40, 57, 36,
   -18, 28, 19, 47, 31, 34, 39, 23,
   -16, -27, 15, 6, 9, 17, 10, 5,
   -22, -23, -30, -16, -16, -23, -36, -32,
   -33, -28, -22, -43, -5, -32, -20, -41,
)

MG_KING_TABLE = (
    -15, 36, 12, -54, 8, -28, 24, 14,
      1, 7, -8, -64, -43, -16, 9, 8,
    -14, -14, -22, -46, -44, -30, -15, -27,
    -49, -1, -27, -39, -46, -44, -33, -51,
    -17, -20, -12, -27, -30, -25, -14, -36,
     -9, 24, 2, -16, -20, 6, 22, -22,
     29, -1, -20, -7, -8, -4, -38, -29,
    -65, 23, 16, -15, -56, -34, 2, 13,
)

EG_KING_TABLE = (
    -74, -35, -18, -18, -11, 15, 4, -17,
    -12, 17, 14, 17, 17, 38, 23, 11,
     10, 17, 23, 15, 20, 45, 44, 13,
     -8, 22, 24, 27, 26, 33, 26, 3,
    -18, -4, 21, 24, 27, 23, 9, -11,
    -19, -3, 11, 21, 23, 16, 7, -9,
    -27, -11, 4, 13, 14, 4, -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43,
)

# fmt: on

# -- Precomputed tables for pawn structure --
_BB_FILES = tuple(0x0101010101010101 << f for f in range(8))
_BB_ADJ_FILES = tuple(
    (_BB_FILES[max(0, f - 1)] if f > 0 else 0) | (_BB_FILES[min(7, f + 1)] if f < 7 else 0)
    for f in range(8)
)

# Ranks above a given rank (for white passed pawn detection)
_RANKS_ABOVE = tuple(
    sum(0xFF << (8 * r) for r in range(rank + 1, 8)) if rank < 7 else 0 for rank in range(8)
)
# Ranks below (for black)
_RANKS_BELOW = tuple(
    sum(0xFF << (8 * r) for r in range(rank)) if rank > 0 else 0 for rank in range(8)
)

# Passed pawn bonus by rank (from white's perspective, rank index 0-7)
_PASSED_PAWN_BONUS_MG = (0, 5, 10, 20, 35, 60, 100, 0)
_PASSED_PAWN_BONUS_EG = (0, 10, 17, 35, 62, 100, 170, 0)

ISOLATED_PAWN_PENALTY_MG = -15
ISOLATED_PAWN_PENALTY_EG = -20
DOUBLED_PAWN_PENALTY_MG = -10
DOUBLED_PAWN_PENALTY_EG = -20
BISHOP_PAIR_BONUS_MG = 30
BISHOP_PAIR_BONUS_EG = 50
ROOK_OPEN_FILE_MG = 25
ROOK_OPEN_FILE_EG = 10
ROOK_SEMI_OPEN_FILE_MG = 12
ROOK_SEMI_OPEN_FILE_EG = 8
ROOK_ON_7TH_MG = 20
ROOK_ON_7TH_EG = 40
TEMPO_BONUS = 0

# Mobility weights per piece type (centipawns per safe square)
MOB_KNIGHT_MG = 4
MOB_KNIGHT_EG = 4
MOB_BISHOP_MG = 5
MOB_BISHOP_EG = 5
MOB_ROOK_MG = 2
MOB_ROOK_EG = 4
MOB_QUEEN_MG = 1
MOB_QUEEN_EG = 2

# King safety: attack units
KING_ATTACK_WEIGHT = (0, 0, 50, 75, 88, 94, 97, 99, 99, 99, 99, 99, 99, 99, 99, 99)
KING_ZONE_ATTACK_UNIT = {KNIGHT: 2, BISHOP: 2, ROOK: 3, QUEEN: 5}

# Knight outpost
KNIGHT_OUTPOST_MG = 25
KNIGHT_OUTPOST_EG = 15

# Backward pawn
BACKWARD_PAWN_PENALTY_MG = -10
BACKWARD_PAWN_PENALTY_EG = -15

# Connected pawn bonus
CONNECTED_PAWN_MG = 7
CONNECTED_PAWN_EG = 5
PAWN_THREAT_MINOR_MG = 18
PAWN_THREAT_MINOR_EG = 12
PAWN_THREAT_ROOK_MG = 28
PAWN_THREAT_ROOK_EG = 18
PAWN_THREAT_QUEEN_MG = 45
PAWN_THREAT_QUEEN_EG = 30
EVAL_SCALE = 1.0

# Combined PST: material + positional, for fast lookup
# _MG_TABLE[piece_type] and _EG_TABLE[piece_type] indexed by square
_MG_TABLE = [None] * 7  # index 0 unused, 1=pawn..6=king
_EG_TABLE = [None] * 7

_MG_VALS = (0, MG_PAWN_VAL, MG_KNIGHT_VAL, MG_BISHOP_VAL, MG_ROOK_VAL, MG_QUEEN_VAL, 0)
_EG_VALS = (0, EG_PAWN_VAL, EG_KNIGHT_VAL, EG_BISHOP_VAL, EG_ROOK_VAL, EG_QUEEN_VAL, 0)
_MG_PSTS = (
    None,
    MG_PAWN_TABLE,
    MG_KNIGHT_TABLE,
    MG_BISHOP_TABLE,
    MG_ROOK_TABLE,
    MG_QUEEN_TABLE,
    MG_KING_TABLE,
)
_EG_PSTS = (
    None,
    EG_PAWN_TABLE,
    EG_KNIGHT_TABLE,
    EG_BISHOP_TABLE,
    EG_ROOK_TABLE,
    EG_QUEEN_TABLE,
    EG_KING_TABLE,
)

for _pt in range(1, 7):
    _MG_TABLE[_pt] = tuple(_MG_VALS[_pt] + _MG_PSTS[_pt][sq] for sq in range(64))
    _EG_TABLE[_pt] = tuple(_EG_VALS[_pt] + _EG_PSTS[_pt][sq] for sq in range(64))

PHASE_BY_TYPE = (0, 0, PHASE_KNIGHT, PHASE_BISHOP, PHASE_ROOK, PHASE_QUEEN, 0)

# Precomputed king zones: squares around king + 1 rank forward
_KING_ZONE = [0] * 64
for _ksq in range(64):
    _zone = KING_ATTACKS[_ksq] | (1 << _ksq)
    # Extend one rank toward the opponent
    _kr = _ksq >> 3
    if _kr < 7:
        _zone |= (_zone << 8) & 0xFFFFFFFFFFFFFFFF
    if _kr > 0:
        _zone |= _zone >> 8
    _KING_ZONE[_ksq] = _zone
_KING_ZONE = tuple(_KING_ZONE)

# White/black 7th rank masks
_BB_RANK_7 = 0xFF << 48
_BB_RANK_2 = 0xFF << 8


def _sum_pst(bitboard: int, table: tuple[int, ...]) -> int:
    total = 0
    while bitboard:
        sq = (bitboard & -bitboard).bit_length() - 1
        total += table[sq]
        bitboard &= bitboard - 1
    return total


def _sum_pst_flip(bitboard: int, table: tuple[int, ...]) -> int:
    """Sum PST values for black pieces (flip square vertically)."""
    total = 0
    while bitboard:
        sq = (bitboard & -bitboard).bit_length() - 1
        total += table[sq ^ 56]
        bitboard &= bitboard - 1
    return total


class ClassicalHeuristic(Heuristic):
    _pawn_hash: dict[int, tuple[int, int, int, int]]

    def __init__(self) -> None:
        super().__init__()
        self._pawn_hash = {}
        self._pawn_hash_size = 32768

    @staticmethod
    def use_quiescence() -> bool:
        return True

    def clear_pawn_hash(self) -> None:
        self._pawn_hash.clear()

    def _evaluate_internal(self, board: Board) -> float:  # noqa: C901, PLR0912, PLR0915
        pb = board._piece_bitboards
        w_pawns = pb[PAWN]
        b_pawns = pb[PAWN + 6]
        w_knights = pb[KNIGHT]
        b_knights = pb[KNIGHT + 6]
        w_bishops = pb[BISHOP]
        b_bishops = pb[BISHOP + 6]
        w_rooks = pb[ROOK]
        b_rooks = pb[ROOK + 6]
        w_queens = pb[QUEEN]
        b_queens = pb[QUEEN + 6]
        w_king_sq = board._king_squares[WHITE]
        b_king_sq = board._king_squares[BLACK]

        # --- Game phase ---
        phase = (
            (w_knights.bit_count() + b_knights.bit_count()) * PHASE_KNIGHT
            + (w_bishops.bit_count() + b_bishops.bit_count()) * PHASE_BISHOP
            + (w_rooks.bit_count() + b_rooks.bit_count()) * PHASE_ROOK
            + (w_queens.bit_count() + b_queens.bit_count()) * PHASE_QUEEN
        )
        phase = min(phase, TOTAL_PHASE)

        # --- Piece-square table scores ---
        mg = (
            _sum_pst(w_pawns, _MG_TABLE[PAWN])
            - _sum_pst_flip(b_pawns, _MG_TABLE[PAWN])
            + _sum_pst(w_knights, _MG_TABLE[KNIGHT])
            - _sum_pst_flip(b_knights, _MG_TABLE[KNIGHT])
            + _sum_pst(w_bishops, _MG_TABLE[BISHOP])
            - _sum_pst_flip(b_bishops, _MG_TABLE[BISHOP])
            + _sum_pst(w_rooks, _MG_TABLE[ROOK])
            - _sum_pst_flip(b_rooks, _MG_TABLE[ROOK])
            + _sum_pst(w_queens, _MG_TABLE[QUEEN])
            - _sum_pst_flip(b_queens, _MG_TABLE[QUEEN])
            + MG_KING_TABLE[w_king_sq]
            - MG_KING_TABLE[b_king_sq ^ 56]
        )
        eg = (
            _sum_pst(w_pawns, _EG_TABLE[PAWN])
            - _sum_pst_flip(b_pawns, _EG_TABLE[PAWN])
            + _sum_pst(w_knights, _EG_TABLE[KNIGHT])
            - _sum_pst_flip(b_knights, _EG_TABLE[KNIGHT])
            + _sum_pst(w_bishops, _EG_TABLE[BISHOP])
            - _sum_pst_flip(b_bishops, _EG_TABLE[BISHOP])
            + _sum_pst(w_rooks, _EG_TABLE[ROOK])
            - _sum_pst_flip(b_rooks, _EG_TABLE[ROOK])
            + _sum_pst(w_queens, _EG_TABLE[QUEEN])
            - _sum_pst_flip(b_queens, _EG_TABLE[QUEEN])
            + EG_KING_TABLE[w_king_sq]
            - EG_KING_TABLE[b_king_sq ^ 56]
        )

        # --- Pawn structure (cached) ---
        pawn_key = w_pawns ^ (b_pawns * 0x9E3779B97F4A7C15 & 0xFFFFFFFFFFFFFFFF)
        cached = self._pawn_hash.get(pawn_key)
        if cached is not None:
            mg_pawn, eg_pawn, w_pawn_attacks, b_pawn_attacks = cached
        else:
            mg_pawn, eg_pawn, w_pawn_attacks, b_pawn_attacks = _evaluate_pawns(w_pawns, b_pawns)
            if len(self._pawn_hash) >= self._pawn_hash_size:
                self._pawn_hash.clear()
            self._pawn_hash[pawn_key] = (mg_pawn, eg_pawn, w_pawn_attacks, b_pawn_attacks)

        mg += mg_pawn
        eg += eg_pawn

        # --- Bishop pair ---
        if w_bishops.bit_count() >= 2:
            mg += BISHOP_PAIR_BONUS_MG
            eg += BISHOP_PAIR_BONUS_EG
        if b_bishops.bit_count() >= 2:
            mg -= BISHOP_PAIR_BONUS_MG
            eg -= BISHOP_PAIR_BONUS_EG

        # --- Rook on open / semi-open file + 7th rank ---
        all_pawns = w_pawns | b_pawns
        bb = w_rooks
        while bb:
            sq = (bb & -bb).bit_length() - 1
            f = sq & 7
            file_mask = _BB_FILES[f]
            if not (all_pawns & file_mask):
                mg += ROOK_OPEN_FILE_MG
                eg += ROOK_OPEN_FILE_EG
            elif not (w_pawns & file_mask):
                mg += ROOK_SEMI_OPEN_FILE_MG
                eg += ROOK_SEMI_OPEN_FILE_EG
            if (1 << sq) & _BB_RANK_7:
                mg += ROOK_ON_7TH_MG
                eg += ROOK_ON_7TH_EG
            bb &= bb - 1

        bb = b_rooks
        while bb:
            sq = (bb & -bb).bit_length() - 1
            f = sq & 7
            file_mask = _BB_FILES[f]
            if not (all_pawns & file_mask):
                mg -= ROOK_OPEN_FILE_MG
                eg -= ROOK_OPEN_FILE_EG
            elif not (b_pawns & file_mask):
                mg -= ROOK_SEMI_OPEN_FILE_MG
                eg -= ROOK_SEMI_OPEN_FILE_EG
            if (1 << sq) & _BB_RANK_2:
                mg -= ROOK_ON_7TH_MG
                eg -= ROOK_ON_7TH_EG
            bb &= bb - 1

        # --- Lightweight mobility + king safety zone ---
        # Only knight mobility (cheap table lookup) + simple king zone
        w_king_zone = _KING_ZONE[b_king_sq]
        b_king_zone = _KING_ZONE[w_king_sq]
        w_attack_units = 0
        b_attack_units = 0

        w_occ = board._occupancy_by_color[WHITE]
        b_occ = board._occupancy_by_color[BLACK]
        w_safe = ~b_pawn_attacks & ~w_occ
        b_safe = ~w_pawn_attacks & ~b_occ

        w_minor_threats = (w_knights | w_bishops) & b_pawn_attacks
        b_minor_threats = (b_knights | b_bishops) & w_pawn_attacks
        mg += (b_minor_threats.bit_count() - w_minor_threats.bit_count()) * PAWN_THREAT_MINOR_MG
        eg += (b_minor_threats.bit_count() - w_minor_threats.bit_count()) * PAWN_THREAT_MINOR_EG
        mg += (
            (b_rooks & w_pawn_attacks).bit_count() - (w_rooks & b_pawn_attacks).bit_count()
        ) * PAWN_THREAT_ROOK_MG
        eg += (
            (b_rooks & w_pawn_attacks).bit_count() - (w_rooks & b_pawn_attacks).bit_count()
        ) * PAWN_THREAT_ROOK_EG
        mg += (
            (b_queens & w_pawn_attacks).bit_count() - (w_queens & b_pawn_attacks).bit_count()
        ) * PAWN_THREAT_QUEEN_MG
        eg += (
            (b_queens & w_pawn_attacks).bit_count() - (w_queens & b_pawn_attacks).bit_count()
        ) * PAWN_THREAT_QUEEN_EG

        # Knight mobility + outpost + king zone (all cheap table lookups)
        bb = w_knights
        while bb:
            sq = (bb & -bb).bit_length() - 1
            attacks = KNIGHT_ATTACKS[sq]
            mob = (attacks & w_safe).bit_count()
            mg += mob * MOB_KNIGHT_MG
            eg += mob * MOB_KNIGHT_EG
            if attacks & w_king_zone:
                w_attack_units += KING_ZONE_ATTACK_UNIT[KNIGHT]
            rank = sq >> 3
            if (
                rank >= 4
                and (PAWN_ATTACKS[BLACK][sq] & w_pawns)
                and not (PAWN_ATTACKS[WHITE][sq] & b_pawns)
            ):
                mg += KNIGHT_OUTPOST_MG
                eg += KNIGHT_OUTPOST_EG
            bb &= bb - 1

        bb = b_knights
        while bb:
            sq = (bb & -bb).bit_length() - 1
            attacks = KNIGHT_ATTACKS[sq]
            mob = (attacks & b_safe).bit_count()
            mg -= mob * MOB_KNIGHT_MG
            eg -= mob * MOB_KNIGHT_EG
            if attacks & b_king_zone:
                b_attack_units += KING_ZONE_ATTACK_UNIT[KNIGHT]
            rank = sq >> 3
            if (
                rank <= 3
                and (PAWN_ATTACKS[WHITE][sq] & b_pawns)
                and not (PAWN_ATTACKS[BLACK][sq] & w_pawns)
            ):
                mg -= KNIGHT_OUTPOST_MG
                eg -= KNIGHT_OUTPOST_EG
            bb &= bb - 1

        occupied = board._occupied
        bb = w_bishops
        while bb:
            sq = (bb & -bb).bit_length() - 1
            mob = (bishop_attacks(sq, occupied) & w_safe).bit_count()
            mg += mob * MOB_BISHOP_MG
            eg += mob * MOB_BISHOP_EG
            bb &= bb - 1

        bb = b_bishops
        while bb:
            sq = (bb & -bb).bit_length() - 1
            mob = (bishop_attacks(sq, occupied) & b_safe).bit_count()
            mg -= mob * MOB_BISHOP_MG
            eg -= mob * MOB_BISHOP_EG
            bb &= bb - 1

        bb = w_rooks
        while bb:
            sq = (bb & -bb).bit_length() - 1
            mob = (rook_attacks(sq, occupied) & w_safe).bit_count()
            mg += mob * MOB_ROOK_MG
            eg += mob * MOB_ROOK_EG
            bb &= bb - 1

        bb = b_rooks
        while bb:
            sq = (bb & -bb).bit_length() - 1
            mob = (rook_attacks(sq, occupied) & b_safe).bit_count()
            mg -= mob * MOB_ROOK_MG
            eg -= mob * MOB_ROOK_EG
            bb &= bb - 1

        bb = w_queens
        while bb:
            sq = (bb & -bb).bit_length() - 1
            mob = (queen_attacks(sq, occupied) & w_safe).bit_count()
            mg += mob * MOB_QUEEN_MG
            eg += mob * MOB_QUEEN_EG
            bb &= bb - 1

        bb = b_queens
        while bb:
            sq = (bb & -bb).bit_length() - 1
            mob = (queen_attacks(sq, occupied) & b_safe).bit_count()
            mg -= mob * MOB_QUEEN_MG
            eg -= mob * MOB_QUEEN_EG
            bb &= bb - 1

        # Cheap king zone: count pieces in enemy king zone via bitboard intersection
        if w_bishops & w_king_zone:
            w_attack_units += KING_ZONE_ATTACK_UNIT[BISHOP]
        if w_rooks & w_king_zone:
            w_attack_units += KING_ZONE_ATTACK_UNIT[ROOK]
        if w_queens & w_king_zone:
            w_attack_units += KING_ZONE_ATTACK_UNIT[QUEEN]

        if b_bishops & b_king_zone:
            b_attack_units += KING_ZONE_ATTACK_UNIT[BISHOP]
        if b_rooks & b_king_zone:
            b_attack_units += KING_ZONE_ATTACK_UNIT[ROOK]
        if b_queens & b_king_zone:
            b_attack_units += KING_ZONE_ATTACK_UNIT[QUEEN]

        # Apply king attack scores
        if w_attack_units > 0:
            idx = min(w_attack_units, len(KING_ATTACK_WEIGHT) - 1)
            mg += KING_ATTACK_WEIGHT[idx]
        if b_attack_units > 0:
            idx = min(b_attack_units, len(KING_ATTACK_WEIGHT) - 1)
            mg -= KING_ATTACK_WEIGHT[idx]

        # --- King safety: pawn shelter ---
        mg += _pawn_shelter_score(w_king_sq, w_pawns, WHITE)
        mg -= _pawn_shelter_score(b_king_sq, b_pawns, BLACK)

        if phase <= 8:
            eg += _king_pawn_distance_bonus(w_king_sq, b_king_sq, w_pawns, b_pawns)

        # --- Tapered eval ---
        evaluation = (mg * phase + eg * (TOTAL_PHASE - phase)) // TOTAL_PHASE

        # --- Mop-up eval: drive enemy king to corner in winning endgames ---
        if phase <= 6:
            if evaluation > 200:
                evaluation += _mop_up_score(b_king_sq, w_king_sq)
            elif evaluation < -200:
                evaluation -= _mop_up_score(w_king_sq, b_king_sq)

        # Tempo bonus
        if board._side_to_move == WHITE:
            return int((evaluation + TEMPO_BONUS) * EVAL_SCALE)
        return int(-(evaluation - TEMPO_BONUS) * EVAL_SCALE)


def _pawn_shelter_score(king_sq: int, friendly_pawns: int, color: int) -> int:
    """Evaluate pawn shelter in front of the king."""
    f = king_sq & 7
    score = 0
    for file_idx in range(max(0, f - 1), min(8, f + 2)):
        file_mask = _BB_FILES[file_idx]
        pawns_on_file = friendly_pawns & file_mask
        if not pawns_on_file:
            score -= 18
            continue
        if color == WHITE:
            # Find the most advanced pawn (highest rank) on this file
            most_advanced_rank = (pawns_on_file.bit_length() - 1) >> 3
            distance = most_advanced_rank - (king_sq >> 3)
        else:
            # Find the least advanced pawn (lowest rank) for black
            least_sq = (pawns_on_file & -pawns_on_file).bit_length() - 1
            distance = (king_sq >> 3) - (least_sq >> 3)
        if distance <= 1:
            score += 12
        elif distance == 2:
            score += 4
        else:
            score -= 8
    return score


# Center distance table for mop-up evaluation
_CENTER_DISTANCE = []
for _sq in range(64):
    _f = (_sq & 7) - 3.5
    _r = (_sq >> 3) - 3.5
    _CENTER_DISTANCE.append(int(abs(_f) + abs(_r)))
_CENTER_DISTANCE = tuple(_CENTER_DISTANCE)


def _mop_up_score(losing_king_sq: int, winning_king_sq: int) -> int:
    """Bonus for pushing losing king to corner and keeping kings close."""
    # Losing king far from center = good
    cmd = _CENTER_DISTANCE[losing_king_sq] * 8
    # Kings close together = good (easier to checkmate)
    kr_diff = abs((winning_king_sq >> 3) - (losing_king_sq >> 3))
    kf_diff = abs((winning_king_sq & 7) - (losing_king_sq & 7))
    close = (14 - kr_diff - kf_diff) * 4
    return cmd + close


def _evaluate_pawns(w_pawns: int, b_pawns: int) -> tuple[int, int, int, int]:  # noqa: C901, PLR0915
    """Evaluate pawn structure and pawn attack maps."""
    mg_pawn = 0
    eg_pawn = 0
    w_pawn_attacks = 0
    b_pawn_attacks = 0
    for f in range(8):
        file_mask = _BB_FILES[f]
        adj_mask = _BB_ADJ_FILES[f]

        wp_on_file = w_pawns & file_mask
        bp_on_file = b_pawns & file_mask

        # Doubled pawns
        wc = wp_on_file.bit_count()
        bc = bp_on_file.bit_count()
        if wc > 1:
            mg_pawn += (wc - 1) * DOUBLED_PAWN_PENALTY_MG
            eg_pawn += (wc - 1) * DOUBLED_PAWN_PENALTY_EG
        if bc > 1:
            mg_pawn -= (bc - 1) * DOUBLED_PAWN_PENALTY_MG
            eg_pawn -= (bc - 1) * DOUBLED_PAWN_PENALTY_EG

        # Isolated pawns
        if wp_on_file and not (w_pawns & adj_mask):
            mg_pawn += wc * ISOLATED_PAWN_PENALTY_MG
            eg_pawn += wc * ISOLATED_PAWN_PENALTY_EG
        if bp_on_file and not (b_pawns & adj_mask):
            mg_pawn -= bc * ISOLATED_PAWN_PENALTY_MG
            eg_pawn -= bc * ISOLATED_PAWN_PENALTY_EG

    # Passed pawns + connected pawns
    bb = w_pawns
    while bb:
        sq = (bb & -bb).bit_length() - 1
        w_pawn_attacks |= PAWN_ATTACKS[WHITE][sq]
        rank = sq >> 3
        f = sq & 7
        mask = (_BB_FILES[f] | _BB_ADJ_FILES[f]) & _RANKS_ABOVE[rank]
        if not (b_pawns & mask):
            mg_pawn += _PASSED_PAWN_BONUS_MG[rank]
            eg_pawn += _PASSED_PAWN_BONUS_EG[rank]
        if PAWN_ATTACKS[BLACK][sq] & w_pawns:
            mg_pawn += CONNECTED_PAWN_MG
            eg_pawn += CONNECTED_PAWN_EG
        bb &= bb - 1

    bb = b_pawns
    while bb:
        sq = (bb & -bb).bit_length() - 1
        b_pawn_attacks |= PAWN_ATTACKS[BLACK][sq]
        rank = sq >> 3
        f = sq & 7
        mask = (_BB_FILES[f] | _BB_ADJ_FILES[f]) & _RANKS_BELOW[rank]
        if not (w_pawns & mask):
            mg_pawn -= _PASSED_PAWN_BONUS_MG[7 - rank]
            eg_pawn -= _PASSED_PAWN_BONUS_EG[7 - rank]
        if PAWN_ATTACKS[WHITE][sq] & b_pawns:
            mg_pawn -= CONNECTED_PAWN_MG
            eg_pawn -= CONNECTED_PAWN_EG
        bb &= bb - 1

    return mg_pawn, eg_pawn, w_pawn_attacks, b_pawn_attacks


def _king_pawn_distance_bonus(w_king_sq: int, b_king_sq: int, w_pawns: int, b_pawns: int) -> int:
    """In endgames, bonus for own king being close to passed pawns."""
    bonus = 0
    # White passed pawns: white king close = good, black king far = good
    bb = w_pawns
    while bb:
        sq = (bb & -bb).bit_length() - 1
        rank = sq >> 3
        f = sq & 7
        mask = (_BB_FILES[f] | _BB_ADJ_FILES[f]) & _RANKS_ABOVE[rank]
        if not (b_pawns & mask):
            # Chebyshev distance
            wr = w_king_sq >> 3
            wf = w_king_sq & 7
            br = b_king_sq >> 3
            bf = b_king_sq & 7
            pr = sq >> 3
            pf = sq & 7
            w_dist = max(abs(wr - pr), abs(wf - pf))
            b_dist = max(abs(br - pr), abs(bf - pf))
            bonus += (b_dist - w_dist) * 5
        bb &= bb - 1

    # Black passed pawns
    bb = b_pawns
    while bb:
        sq = (bb & -bb).bit_length() - 1
        rank = sq >> 3
        f = sq & 7
        mask = (_BB_FILES[f] | _BB_ADJ_FILES[f]) & _RANKS_BELOW[rank]
        if not (w_pawns & mask):
            wr = w_king_sq >> 3
            wf = w_king_sq & 7
            br = b_king_sq >> 3
            bf = b_king_sq & 7
            pr = sq >> 3
            pf = sq & 7
            w_dist = max(abs(wr - pr), abs(wf - pf))
            b_dist = max(abs(br - pr), abs(bf - pf))
            bonus -= (w_dist - b_dist) * 5
        bb &= bb - 1

    return bonus
