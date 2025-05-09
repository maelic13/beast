from chess import BISHOP, BLACK, KNIGHT, PAWN, QUEEN, ROOK, WHITE, Board, SquareSet

from beast.heuristics.heuristic import Heuristic
from beast.heuristics.piece_values import PieceValues


class ClassicalHeuristic(Heuristic):
    # Parameter weights for bonus eval
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

    @staticmethod
    def use_quiescence() -> bool:
        """
        Whether to use quiescence search with this heuristic.
        :return: use quiescence or not
        """
        return True

    def _evaluate_internal(self, board: Board) -> float:  # noqa: PLR0914
        """
        Classical style heuristic function based on piece values and derived from human knowledge.
        :param board: board representation
        :return: position evaluation
        """

        # TODO: improve, at the very least make it from point of view of player to move

        # pieces
        w_pawns = board.pieces(PAWN, WHITE)
        b_pawns = board.pieces(PAWN, BLACK)
        w_knights = board.pieces(KNIGHT, WHITE)
        b_knights = board.pieces(KNIGHT, BLACK)
        w_bishops = board.pieces(BISHOP, WHITE)
        b_bishops = board.pieces(BISHOP, BLACK)
        w_rooks = board.pieces(ROOK, WHITE)
        b_rooks = board.pieces(ROOK, BLACK)
        w_queens = board.pieces(QUEEN, WHITE)
        b_queens = board.pieces(QUEEN, BLACK)
        w_king = board.king(WHITE)
        b_king = board.king(BLACK)

        # Initial eval - adding value of pieces on board
        evaluation = (
            len(w_pawns) * PieceValues.PAWN_VALUE
            - len(b_pawns) * PieceValues.PAWN_VALUE
            + len(w_knights) * PieceValues.KNIGHT_VALUE
            - len(b_knights) * PieceValues.KNIGHT_VALUE
            + len(w_bishops) * PieceValues.BISHOP_VALUE
            - len(b_bishops) * PieceValues.BISHOP_VALUE
            + len(w_rooks) * PieceValues.ROOK_VALUE
            - len(b_rooks) * PieceValues.ROOK_VALUE
            + len(w_queens) * PieceValues.QUEEN_VALUE
            - len(b_queens) * PieceValues.QUEEN_VALUE
        )

        # Pawns
        wp_bonus = self._pawn_bonus(w_pawns, b_king, color=True)
        bp_bonus = self._pawn_bonus(b_pawns, w_king, color=False)

        # Knights
        wk_bonus = self._knight_bonus(w_knights, b_king)
        bk_bonus = self._knight_bonus(b_knights, w_king)

        # Bishops
        wb_bonus = self._bishop_bonus(w_bishops, b_king)
        bb_bonus = self._bishop_bonus(b_bishops, w_king)

        # Rooks
        wr_bonus = self._rook_bonus(w_rooks, b_king)
        br_bonus = self._rook_bonus(b_rooks, w_king)

        # Queens
        wq_bonus = self._queen_bonus(w_queens, b_king)
        bq_bonus = self._queen_bonus(b_queens, w_king)

        # Kings
        wki_bonus = self._king_bonus(w_king, b_king, no_queen=bool(b_queens))
        bki_bonus = self._king_bonus(b_king, w_king, no_queen=bool(w_queens))

        # Add bonuses to eval
        evaluation += (
            wp_bonus
            - bp_bonus
            + wk_bonus
            - bk_bonus
            + wb_bonus
            - bb_bonus
            + wr_bonus
            - br_bonus
            + wq_bonus
            - bq_bonus
            + wki_bonus
            - bki_bonus
        )

        if not board.turn:
            return int(-evaluation)
        return int(evaluation)

    def _pawn_bonus(self, pawns: SquareSet, king_position: int, *, color: bool) -> int:
        """
        Evaluation bonus for positions of pawns on board.
        :param pawns: set of squares containing pawns
        :param king_position: opponent king's position on board
        :param color: player to move, white True, black False
        :return: evaluation bonus
        """
        p_bonus = 0
        for pawn_position in pawns:
            # rank bonus -> the further forward the pawn, the more of a bonus
            if color:
                p_bonus += (int(pawn_position / 8) - 1) * self.PAWN_RANK_WEIGHT
            else:
                p_bonus += (6 - int(pawn_position / 8)) * self.PAWN_RANK_WEIGHT

            # file penalty -> central files take none, the closer to rim the less pawn's value
            if pawn_position % 8 < 3:
                p_bonus -= (3 - pawn_position % 8) * self.PAWN_FILE_WEIGHT
            elif pawn_position % 8 > 4:
                p_bonus -= (pawn_position % 8 - 4) * self.PAWN_FILE_WEIGHT

            # occupying center bonus
            p_bonus += self._occupying_center_bonus(pawn_position, self.PAWN_CENTER_WEIGHT)
            # distance from king bonus
            p_bonus += self._distance_from_king_bonus(
                pawn_position, king_position, self.PAWN_DISTANCE_WEIGHT
            )

        return p_bonus

    def _knight_bonus(self, knights: SquareSet, king_position: int) -> int:
        """
        Evaluation bonus for positions knights on board.
        :param knights: set of squares containing knights
        :param king_position: opponent king's position on board
        :return: evaluation bonus
        """
        k_bonus = 0
        for knight_position in knights:
            # occupying center bonus
            k_bonus += self._occupying_center_bonus(knight_position, self.KNIGHT_CENTER_WEIGHT)

            # distance from king bonus
            k_bonus += self._distance_from_king_bonus(
                knight_position, king_position, self.KNIGHT_DISTANCE_WEIGHT
            )

        return k_bonus

    def _bishop_bonus(self, bishops: SquareSet, king_position: int) -> int:
        """
        Evaluation bonus for positions of bishops on board.
        :param bishops: set of squares containing bishops
        :param king_position: opponent king's position on board
        :return: evaluation bonus
        """
        b_bonus = 0
        for bishop_position in bishops:
            # occupying center bonus
            b_bonus += self._occupying_center_bonus(bishop_position, self.BISHOP_CENTER_WEIGHT)

            # distance from king bonus
            b_bonus += self._distance_from_king_bonus(
                bishop_position, king_position, self.KNIGHT_DISTANCE_WEIGHT
            )

        return b_bonus

    def _rook_bonus(self, rooks: SquareSet, king_position: int) -> int:
        """
        Evaluation bonus for positions of rooks on board.
        :param rooks: set of squares containing rooks
        :param king_position: opponent king's position on board
        :return: evaluation bonus
        """
        r_bonus = 0
        for rook_position in rooks:
            # occupying center files bonus
            if rook_position % 8 in range(3, 5):
                r_bonus += self.ROOK_CENTER_WEIGHT
            if rook_position % 8 in range(2, 6):
                r_bonus += self.ROOK_CENTER_WEIGHT
            if rook_position % 8 in range(1, 7):
                r_bonus += self.ROOK_CENTER_WEIGHT

            # distance from king bonus
            r_bonus += self._distance_from_king_bonus(
                rook_position, king_position, self.ROOK_DISTANCE_WEIGHT
            )

        return r_bonus

    def _queen_bonus(self, queens: SquareSet, king_position: int) -> int:
        """
        Evaluation bonus for positions of queens on board.
        :param queens: set of squares containing queens
        :param king_position: opponent king's position on board
        :return: evaluation bonus
        """
        q_bonus = 0
        for queen_position in queens:
            # occupying center bonus
            q_bonus += self._occupying_center_bonus(queen_position, self.QUEEN_CENTER_WEIGHT)

            # distance from king bonus
            q_bonus += self._distance_from_king_bonus(
                queen_position, king_position, self.QUEEN_DISTANCE_WEIGHT
            )

        return q_bonus

    def _king_bonus(self, king_position: int, opponents_king: int, *, no_queen: bool) -> int:
        """
        Evaluation bonus for positions of king on board.
        :param king_position: king's position on board
        :param opponents_king: opponent king's position on board
        :param no_queen: information about the presence of opponent's queens on board
        :return: evaluation bonus
        """
        k_bonus = 0
        king_center_weight = self.KING_CENTER_WEIGHT if no_queen else -self.KING_CENTER_WEIGHT

        # occupying center bonus
        k_bonus += self._occupying_center_bonus(king_position, king_center_weight)

        # distance from king bonus
        k_bonus += self._distance_from_king_bonus(
            king_position, opponents_king, self.KING_DISTANCE_WEIGHT
        )

        return k_bonus

    @staticmethod
    def _occupying_center_bonus(piece_position: int, bonus: int) -> int:
        """
        Bonus for occupying squares close to center.
        :param piece_position: position of piece to evaluate
        :param bonus: bonus value for piece type
        :return: evaluation bonus
        """
        if int(piece_position / 8) in range(3, 5) and piece_position % 8 in range(3, 5):
            return 3 * bonus
        if int(piece_position / 8) in range(2, 6) and piece_position % 8 in range(2, 6):
            return 2 * bonus
        if int(piece_position / 8) in range(1, 7) and piece_position % 8 in range(1, 7):
            return bonus
        return 0

    @staticmethod
    def _distance_from_king_bonus(piece_position: int, king_position: int, bonus: int) -> int:
        """
        Bonus for distance from opponent's king.
        :param piece_position: position of piece to evaluate
        :param king_position: opponent king's position
        :param bonus: bonus value for piece type
        :return: evaluation bonus
        """
        distance = abs(int(piece_position / 8) - int(king_position / 8)) + abs(
            piece_position % 8 - king_position % 8
        )
        return int(14 / distance * bonus - bonus)
