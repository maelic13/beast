# ruff: noqa: SLF001
from beast_chess.board import BISHOP, BLACK, KNIGHT, PAWN, QUEEN, ROOK, Board

from .infra import Heuristic, PieceValues

PAWN_RANK_WEIGHT = 7
PAWN_FILE_WEIGHT = 5
PAWN_CENTER_WEIGHT = 5
PAWN_DISTANCE_WEIGHT = 5

KNIGHT_CENTER_WEIGHT = 7
KNIGHT_DISTANCE_WEIGHT = 8

BISHOP_CENTER_WEIGHT = 5
BISHOP_DISTANCE_WEIGHT = 8

ROOK_CENTER_WEIGHT = 8
ROOK_DISTANCE_WEIGHT = 5

QUEEN_CENTER_WEIGHT = 2
QUEEN_DISTANCE_WEIGHT = 8

KING_CENTER_WEIGHT = 8
KING_DISTANCE_WEIGHT = 5


def _center_coefficient(square: int) -> int:
    rank = square >> 3
    file_index = square & 7
    if 3 <= rank <= 4 and 3 <= file_index <= 4:
        return 3
    if 2 <= rank <= 5 and 2 <= file_index <= 5:
        return 2
    if 1 <= rank <= 6 and 1 <= file_index <= 6:
        return 1
    return 0


def _distance_table(weight: int) -> tuple[tuple[int, ...], ...]:
    table: list[tuple[int, ...]] = []
    for square in range(64):
        rank = square >> 3
        file_index = square & 7
        values = []
        for king_square in range(64):
            distance = abs(rank - (king_square >> 3)) + abs(file_index - (king_square & 7))
            values.append(0 if distance == 0 else int(14 / distance * weight - weight))
        table.append(tuple(values))
    return tuple(table)


_CENTER_COEFFICIENTS = tuple(_center_coefficient(square) for square in range(64))
_DISTANCE_WEIGHT_5 = _distance_table(5)
_DISTANCE_WEIGHT_8 = _distance_table(8)
_WHITE_PAWN_TABLE = tuple(
    ((square >> 3) - 1) * PAWN_RANK_WEIGHT
    - (max(0, 3 - (square & 7)) + max(0, (square & 7) - 4)) * PAWN_FILE_WEIGHT
    + _CENTER_COEFFICIENTS[square] * PAWN_CENTER_WEIGHT
    for square in range(64)
)
_BLACK_PAWN_TABLE = tuple(
    (6 - (square >> 3)) * PAWN_RANK_WEIGHT
    - (max(0, 3 - (square & 7)) + max(0, (square & 7) - 4)) * PAWN_FILE_WEIGHT
    + _CENTER_COEFFICIENTS[square] * PAWN_CENTER_WEIGHT
    for square in range(64)
)
_KNIGHT_TABLE = tuple(_CENTER_COEFFICIENTS[square] * KNIGHT_CENTER_WEIGHT for square in range(64))
_BISHOP_TABLE = tuple(_CENTER_COEFFICIENTS[square] * BISHOP_CENTER_WEIGHT for square in range(64))
_ROOK_TABLE = tuple(
    (
        (ROOK_CENTER_WEIGHT if 3 <= (square & 7) <= 4 else 0)
        + (ROOK_CENTER_WEIGHT if 2 <= (square & 7) <= 5 else 0)
        + (ROOK_CENTER_WEIGHT if 1 <= (square & 7) <= 6 else 0)
    )
    for square in range(64)
)
_QUEEN_TABLE = tuple(_CENTER_COEFFICIENTS[square] * QUEEN_CENTER_WEIGHT for square in range(64))
_KING_CENTER_TABLE = tuple(
    _CENTER_COEFFICIENTS[square] * KING_CENTER_WEIGHT for square in range(64)
)
_MATERIAL_VALUES = (
    0,
    PieceValues.PAWN_VALUE,
    PieceValues.KNIGHT_VALUE,
    PieceValues.BISHOP_VALUE,
    PieceValues.ROOK_VALUE,
    PieceValues.QUEEN_VALUE,
)


def _sum_table_and_distance(
    bitboard: int,
    table: tuple[int, ...],
    distance_table: tuple[tuple[int, ...], ...],
    king_square: int,
) -> int:
    total = 0
    while bitboard:
        bit = bitboard & -bitboard
        square = bit.bit_length() - 1
        total += table[square] + distance_table[square][king_square]
        bitboard ^= bit
    return total


class ClassicalHeuristic(Heuristic):
    @staticmethod
    def use_quiescence() -> bool:
        """
        Whether to use quiescence search with this heuristic.
        :return: Use quiescence or not
        """
        return True

    def _evaluate_internal(self, board: Board) -> float:  # noqa: PLR6301
        """
        Classical style heuristic function based on piece values and derived from human knowledge.
        :param board: board representation
        :return: position evaluation
        """

        piece_bitboards = board._piece_bitboards
        king_squares = board._king_squares
        w_pawns = piece_bitboards[PAWN]
        b_pawns = piece_bitboards[PAWN + 6]
        w_knights = piece_bitboards[KNIGHT]
        b_knights = piece_bitboards[KNIGHT + 6]
        w_bishops = piece_bitboards[BISHOP]
        b_bishops = piece_bitboards[BISHOP + 6]
        w_rooks = piece_bitboards[ROOK]
        b_rooks = piece_bitboards[ROOK + 6]
        w_queens = piece_bitboards[QUEEN]
        b_queens = piece_bitboards[QUEEN + 6]
        w_king = king_squares[0]
        b_king = king_squares[1]

        evaluation = (
            (w_pawns.bit_count() - b_pawns.bit_count()) * _MATERIAL_VALUES[PAWN]
            + (w_knights.bit_count() - b_knights.bit_count()) * _MATERIAL_VALUES[KNIGHT]
            + (w_bishops.bit_count() - b_bishops.bit_count()) * _MATERIAL_VALUES[BISHOP]
            + (w_rooks.bit_count() - b_rooks.bit_count()) * _MATERIAL_VALUES[ROOK]
            + (w_queens.bit_count() - b_queens.bit_count()) * _MATERIAL_VALUES[QUEEN]
            + _sum_table_and_distance(w_pawns, _WHITE_PAWN_TABLE, _DISTANCE_WEIGHT_5, b_king)
            - _sum_table_and_distance(b_pawns, _BLACK_PAWN_TABLE, _DISTANCE_WEIGHT_5, w_king)
            + _sum_table_and_distance(w_knights, _KNIGHT_TABLE, _DISTANCE_WEIGHT_8, b_king)
            - _sum_table_and_distance(b_knights, _KNIGHT_TABLE, _DISTANCE_WEIGHT_8, w_king)
            + _sum_table_and_distance(w_bishops, _BISHOP_TABLE, _DISTANCE_WEIGHT_8, b_king)
            - _sum_table_and_distance(b_bishops, _BISHOP_TABLE, _DISTANCE_WEIGHT_8, w_king)
            + _sum_table_and_distance(w_rooks, _ROOK_TABLE, _DISTANCE_WEIGHT_5, b_king)
            - _sum_table_and_distance(b_rooks, _ROOK_TABLE, _DISTANCE_WEIGHT_5, w_king)
            + _sum_table_and_distance(w_queens, _QUEEN_TABLE, _DISTANCE_WEIGHT_8, b_king)
            - _sum_table_and_distance(b_queens, _QUEEN_TABLE, _DISTANCE_WEIGHT_8, w_king)
            + _KING_CENTER_TABLE[w_king] * (-1 if b_queens else 1)
            - _KING_CENTER_TABLE[b_king] * (-1 if w_queens else 1)
            + _DISTANCE_WEIGHT_5[w_king][b_king]
            - _DISTANCE_WEIGHT_5[b_king][w_king]
        )

        if board._side_to_move == BLACK:
            return int(-evaluation)
        return int(evaluation)
