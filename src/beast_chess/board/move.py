from __future__ import annotations

from typing import NewType

from .constants import NO_PIECE, PROMOTION_PIECES, parse_square, piece_symbol, square_name

Move = NewType("Move", int)

NULL_MOVE = Move(-1)

QUIET = 0
CAPTURE = 1
DOUBLE_PAWN_PUSH = 2
EN_PASSANT = 4
CASTLING = 8
PROMOTION = 16

_FROM_MASK = 0x3F
_TO_SHIFT = 6
_PROMOTION_SHIFT = 12
_FLAGS_SHIFT = 15
_SQUARE_MASK = 0x3F
_PROMOTION_MASK = 0x7


def encode_move(
    source: int,
    target: int,
    promotion: int = NO_PIECE,
    flags: int = QUIET,
) -> Move:
    if promotion != NO_PIECE:
        flags |= PROMOTION
    return Move(
        source | (target << _TO_SHIFT) | (promotion << _PROMOTION_SHIFT) | (flags << _FLAGS_SHIFT)
    )


def from_square(move: Move) -> int:
    return int(move) & _FROM_MASK


def to_square(move: Move) -> int:
    return (int(move) >> _TO_SHIFT) & _SQUARE_MASK


def promotion_piece(move: Move) -> int:
    return (int(move) >> _PROMOTION_SHIFT) & _PROMOTION_MASK


def move_flags(move: Move) -> int:
    return int(move) >> _FLAGS_SHIFT


def is_capture(move: Move) -> bool:
    return bool(move_flags(move) & CAPTURE)


def is_double_pawn_push(move: Move) -> bool:
    return bool(move_flags(move) & DOUBLE_PAWN_PUSH)


def is_en_passant(move: Move) -> bool:
    return bool(move_flags(move) & EN_PASSANT)


def is_castling(move: Move) -> bool:
    return bool(move_flags(move) & CASTLING)


def is_promotion(move: Move) -> bool:
    return promotion_piece(move) != NO_PIECE


def same_move(left: Move, right: Move) -> bool:
    return (
        from_square(left) == from_square(right)
        and to_square(left) == to_square(right)
        and promotion_piece(left) == promotion_piece(right)
    )


def uci(move: Move) -> str:
    if move == NULL_MOVE:
        return "0000"
    promotion = promotion_piece(move)
    promotion_suffix = piece_symbol(promotion).lower() if promotion in PROMOTION_PIECES else ""
    return f"{square_name(from_square(move))}{square_name(to_square(move))}{promotion_suffix}"


def parse_uci_squares(value: str) -> tuple[int, int, int]:
    if value == "0000":
        return -1, -1, NO_PIECE
    if len(value) not in {4, 5}:
        msg = f"Invalid UCI move: {value}"
        raise ValueError(msg)

    promotion = NO_PIECE
    if len(value) == 5:
        promotion_symbols = {"n": 2, "b": 3, "r": 4, "q": 5}
        try:
            promotion = promotion_symbols[value[4].lower()]
        except KeyError as err:
            msg = f"Invalid promotion piece in UCI move: {value}"
            raise ValueError(msg) from err

    return parse_square(value[:2]), parse_square(value[2:4]), promotion
