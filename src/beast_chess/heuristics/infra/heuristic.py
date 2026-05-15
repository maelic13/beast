from abc import ABC, abstractmethod
from math import log10

from beast_chess.board import Board


class Heuristic(ABC):
    def __init__(self) -> None:
        # precalculate win and loss values (speed-up of heuristic)
        self.draw_value = self.probability_to_centipawn(0.5) * 100  # [cp]
        self.loss_value = self.probability_to_centipawn(0.0) * 100  # [cp]
        self.win_value = self.probability_to_centipawn(1.0) * 100  # [cp]

    def evaluate_result(self, board: Board, depth: int) -> float:
        if board.is_check():
            return self.loss_value - 100 * depth

        return self.draw_value

    def evaluate_position(self, board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
        if board.is_fifty_moves() or board.is_repetition() or board.has_insufficient_material():
            return self.draw_value

        return self._evaluate_internal(board)

    @staticmethod
    def centipawn_to_probability(centipawn: int) -> float:
        """
        Calculate winning probability given pawn advantage.
        :param centipawn: position value in centipawns
        :return: winning probability
        """
        return 1 / (1 + 10 ** (-(centipawn / 100) / 4))

    @staticmethod
    def probability_to_centipawn(win_probability: float) -> float:
        """
        Calculate pawn advantage given winning probability.
        :param win_probability: win probability (0.0 to 1.0)
        :return: advantage in pawns
        """
        if win_probability <= 0:
            win_probability = 1e-9
        elif win_probability >= 1:
            win_probability = 1.0 - 1e-9
        return 4 * log10(win_probability / (1 - win_probability)) * 100

    @abstractmethod
    def _evaluate_internal(self, board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
