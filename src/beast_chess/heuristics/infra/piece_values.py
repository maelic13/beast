from beast_chess.board import BISHOP, KNIGHT, PAWN, QUEEN, ROOK


class PieceValues:
    """Values of chess pieces - averaged from PeSTO MG/EG values.
    Used for SEE, move ordering, and delta pruning.
    """

    PAWN_VALUE = 88
    KNIGHT_VALUE = 309
    BISHOP_VALUE = 331
    ROOK_VALUE = 495
    QUEEN_VALUE = 981

    @classmethod
    def as_dict(cls) -> dict[int, int]:
        """Return piece values as dictionary.
        :return: piece types and their values
        """
        return {
            PAWN: cls.PAWN_VALUE,
            KNIGHT: cls.KNIGHT_VALUE,
            BISHOP: cls.BISHOP_VALUE,
            ROOK: cls.ROOK_VALUE,
            QUEEN: cls.QUEEN_VALUE,
        }
