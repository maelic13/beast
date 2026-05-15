from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

from .constants import (
    BB_SQUARES,
    BISHOP,
    BLACK,
    KING,
    KNIGHT,
    PAWN,
    QUEEN,
    ROOK,
    WHITE,
    file_of,
    piece_code,
    rank_of,
)

Direction = tuple[int, int]

ROOK_DIRECTIONS: tuple[Direction, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))
BISHOP_DIRECTIONS: tuple[Direction, ...] = ((1, 1), (1, -1), (-1, 1), (-1, -1))
KNIGHT_OFFSETS: tuple[Direction, ...] = (
    (1, 2),
    (2, 1),
    (2, -1),
    (1, -2),
    (-1, -2),
    (-2, -1),
    (-2, 1),
    (-1, 2),
)
KING_OFFSETS: tuple[Direction, ...] = (
    (1, 1),
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


def iter_bits(bitboard: int) -> Iterator[int]:
    while bitboard:
        bit = bitboard & -bitboard
        yield bit.bit_length() - 1
        bitboard ^= bit


def popcount(bitboard: int) -> int:
    return bitboard.bit_count()


def _offset_attacks(square: int, offsets: Iterable[Direction]) -> int:
    attacks = 0
    file_index = file_of(square)
    rank_index = rank_of(square)
    for file_delta, rank_delta in offsets:
        target_file = file_index + file_delta
        target_rank = rank_index + rank_delta
        if 0 <= target_file < 8 and 0 <= target_rank < 8:
            attacks |= BB_SQUARES[target_rank * 8 + target_file]
    return attacks


def _pawn_attacks(color: int, square: int) -> int:
    rank_delta = 1 if color == WHITE else -1
    return _offset_attacks(square, ((-1, rank_delta), (1, rank_delta)))


def _sliding_attacks(square: int, occupied: int, directions: Iterable[Direction]) -> int:
    attacks = 0
    source_file = file_of(square)
    source_rank = rank_of(square)
    for file_delta, rank_delta in directions:
        target_file = source_file + file_delta
        target_rank = source_rank + rank_delta
        while 0 <= target_file < 8 and 0 <= target_rank < 8:
            target = target_rank * 8 + target_file
            target_bit = BB_SQUARES[target]
            attacks |= target_bit
            if occupied & target_bit:
                break
            target_file += file_delta
            target_rank += rank_delta
    return attacks


def _sliding_mask(square: int, directions: Iterable[Direction]) -> int:
    mask = 0
    source_file = file_of(square)
    source_rank = rank_of(square)
    for file_delta, rank_delta in directions:
        target_file = source_file + file_delta
        target_rank = source_rank + rank_delta
        while 0 <= target_file < 8 and 0 <= target_rank < 8:
            next_file = target_file + file_delta
            next_rank = target_rank + rank_delta
            if not (0 <= next_file < 8 and 0 <= next_rank < 8):
                break
            mask |= BB_SQUARES[target_rank * 8 + target_file]
            target_file = next_file
            target_rank = next_rank
    return mask


def _iter_subsets(mask: int) -> Iterator[int]:
    subset = mask
    while True:
        yield subset
        if subset == 0:
            break
        subset = (subset - 1) & mask


def _build_attack_tables(
    directions: Iterable[Direction],
) -> tuple[tuple[int, ...], tuple[dict[int, int], ...]]:
    masks: list[int] = []
    tables: list[dict[int, int]] = []
    for square in range(64):
        mask = _sliding_mask(square, directions)
        masks.append(mask)
        table = {
            blockers: _sliding_attacks(square, blockers, directions)
            for blockers in _iter_subsets(mask)
        }
        tables.append(table)
    return tuple(masks), tuple(tables)


PAWN_ATTACKS = (
    tuple(_pawn_attacks(WHITE, square) for square in range(64)),
    tuple(_pawn_attacks(BLACK, square) for square in range(64)),
)

KNIGHT_ATTACKS = tuple(_offset_attacks(square, KNIGHT_OFFSETS) for square in range(64))

KING_ATTACKS = tuple(_offset_attacks(square, KING_OFFSETS) for square in range(64))

BISHOP_MASKS, BISHOP_ATTACKS = _build_attack_tables(BISHOP_DIRECTIONS)
ROOK_MASKS, ROOK_ATTACKS = _build_attack_tables(ROOK_DIRECTIONS)
BISHOP_RAYS = tuple(_sliding_attacks(square, 0, BISHOP_DIRECTIONS) for square in range(64))
ROOK_RAYS = tuple(_sliding_attacks(square, 0, ROOK_DIRECTIONS) for square in range(64))


def bishop_attacks(square: int, occupied: int) -> int:
    return BISHOP_ATTACKS[square][occupied & BISHOP_MASKS[square]]


def rook_attacks(square: int, occupied: int) -> int:
    return ROOK_ATTACKS[square][occupied & ROOK_MASKS[square]]


def queen_attacks(square: int, occupied: int) -> int:
    return bishop_attacks(square, occupied) | rook_attacks(square, occupied)


ATTACK_FUNCTIONS = {
    piece_code(WHITE, PAWN): lambda square, _occupied: PAWN_ATTACKS[WHITE][square],
    piece_code(BLACK, PAWN): lambda square, _occupied: PAWN_ATTACKS[BLACK][square],
    piece_code(WHITE, KNIGHT): lambda square, _occupied: KNIGHT_ATTACKS[square],
    piece_code(BLACK, KNIGHT): lambda square, _occupied: KNIGHT_ATTACKS[square],
    piece_code(WHITE, BISHOP): bishop_attacks,
    piece_code(BLACK, BISHOP): bishop_attacks,
    piece_code(WHITE, ROOK): rook_attacks,
    piece_code(BLACK, ROOK): rook_attacks,
    piece_code(WHITE, QUEEN): queen_attacks,
    piece_code(BLACK, QUEEN): queen_attacks,
    piece_code(WHITE, KING): lambda square, _occupied: KING_ATTACKS[square],
    piece_code(BLACK, KING): lambda square, _occupied: KING_ATTACKS[square],
}
