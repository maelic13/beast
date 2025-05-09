from chess import BISHOP, KNIGHT, PAWN, QUEEN, ROOK


class PieceValues:
    """
    Values of chess pieces based on human theory.
    """

    PAWN_VALUE = 100
    KNIGHT_VALUE = 350
    BISHOP_VALUE = 370
    ROOK_VALUE = 550
    QUEEN_VALUE = 950

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
        }
