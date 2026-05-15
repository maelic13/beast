from __future__ import annotations

WHITE = 0
BLACK = 1

NO_PIECE = 0
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

PIECE_TYPES = (PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING)
PROMOTION_PIECES = (QUEEN, ROOK, BISHOP, KNIGHT)

NO_SQUARE = -1

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

BB_ALL = (1 << 64) - 1
BB_SQUARES = tuple(1 << square for square in range(64))

FILES = "abcdefgh"
RANKS = "12345678"
SQUARE_NAMES = tuple(f"{file_name}{rank_name}" for rank_name in RANKS for file_name in FILES)

BB_FILE_A = sum(1 << (rank * 8) for rank in range(8))
BB_FILE_B = BB_FILE_A << 1
BB_FILE_G = BB_FILE_A << 6
BB_FILE_H = BB_FILE_A << 7
BB_RANK_1 = 0xFF
BB_RANK_2 = BB_RANK_1 << 8
BB_RANK_3 = BB_RANK_1 << 16
BB_RANK_6 = BB_RANK_1 << 40
BB_RANK_7 = BB_RANK_1 << 48
BB_RANK_8 = BB_RANK_1 << 56

NOT_FILE_A = BB_ALL ^ BB_FILE_A
NOT_FILE_H = BB_ALL ^ BB_FILE_H

A1 = 0
B1 = 1
C1 = 2
D1 = 3
E1 = 4
F1 = 5
G1 = 6
H1 = 7
A8 = 56
B8 = 57
C8 = 58
D8 = 59
E8 = 60
F8 = 61
G8 = 62
H8 = 63

WHITE_KINGSIDE = 1
WHITE_QUEENSIDE = 2
BLACK_KINGSIDE = 4
BLACK_QUEENSIDE = 8
ALL_CASTLING_RIGHTS = WHITE_KINGSIDE | WHITE_QUEENSIDE | BLACK_KINGSIDE | BLACK_QUEENSIDE

CASTLING_RIGHTS_MASKS = [ALL_CASTLING_RIGHTS] * 64
CASTLING_RIGHTS_MASKS[A1] &= ~WHITE_QUEENSIDE
CASTLING_RIGHTS_MASKS[E1] &= ~(WHITE_KINGSIDE | WHITE_QUEENSIDE)
CASTLING_RIGHTS_MASKS[H1] &= ~WHITE_KINGSIDE
CASTLING_RIGHTS_MASKS[A8] &= ~BLACK_QUEENSIDE
CASTLING_RIGHTS_MASKS[E8] &= ~(BLACK_KINGSIDE | BLACK_QUEENSIDE)
CASTLING_RIGHTS_MASKS[H8] &= ~BLACK_KINGSIDE


def opposite(color: int) -> int:
    return color ^ 1


def piece_code(color: int, piece: int) -> int:
    return piece + (6 if color == BLACK else 0)


def piece_color(piece: int) -> int:
    if piece == NO_PIECE:
        msg = "Empty squares do not have a color."
        raise ValueError(msg)
    return BLACK if piece > KING else WHITE


def piece_type(piece: int) -> int:
    if piece == NO_PIECE:
        return NO_PIECE
    return ((piece - 1) % 6) + 1


_PIECE_SYMBOLS = {
    piece_code(WHITE, PAWN): "P",
    piece_code(WHITE, KNIGHT): "N",
    piece_code(WHITE, BISHOP): "B",
    piece_code(WHITE, ROOK): "R",
    piece_code(WHITE, QUEEN): "Q",
    piece_code(WHITE, KING): "K",
    piece_code(BLACK, PAWN): "p",
    piece_code(BLACK, KNIGHT): "n",
    piece_code(BLACK, BISHOP): "b",
    piece_code(BLACK, ROOK): "r",
    piece_code(BLACK, QUEEN): "q",
    piece_code(BLACK, KING): "k",
}

SYMBOL_TO_PIECE = {symbol: piece for piece, symbol in _PIECE_SYMBOLS.items()}


def piece_symbol(piece: int) -> str:
    return _PIECE_SYMBOLS[piece]


def file_of(square: int) -> int:
    return square & 7


def rank_of(square: int) -> int:
    return square >> 3


def square_name(square: int) -> str:
    return SQUARE_NAMES[square]


def parse_square(name: str) -> int:
    if len(name) != 2 or name[0] not in FILES or name[1] not in RANKS:
        msg = f"Invalid square: {name}"
        raise ValueError(msg)
    return RANKS.index(name[1]) * 8 + FILES.index(name[0])
