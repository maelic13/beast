from chess import BISHOP, KNIGHT, PAWN, QUEEN, ROOK, KING


class PieceValues:
    """
    Values of chess pieces based on human theory.
    """

    PAWN_VALUE = 100
    KNIGHT_VALUE = 320
    BISHOP_VALUE = 330
    ROOK_VALUE = 500
    QUEEN_VALUE = 900
    KING_VALUE = 0

    @classmethod
    def as_dict(cls) -> dict[int, int]:
        """
        Return piece values as dictionary.
        :return: piece types and their values
        """
        return {
            PAWN: cls.PAWN_VALUE,
            KNIGHT: cls.KNIGHT_VALUE,
            BISHOP: cls.BISHOP_VALUE,
            ROOK: cls.ROOK_VALUE,
            QUEEN: cls.QUEEN_VALUE,
            KING: cls.KING_VALUE,
        }
