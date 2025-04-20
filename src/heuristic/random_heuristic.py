from random import randint

from chess import Board

from .heuristic import Heuristic


class RandomHeuristic(Heuristic):
    """Random heuristic."""

    @staticmethod
    def use_quiescence() -> bool:
        """
        Whether to use quiescence search with this heuristic.
        :return: use quiescence or not
        """
        return False

    def evaluate(self, board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
        return self._evaluate_internal(board)

    def _evaluate_internal(self, _board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param _board: chess board representation
        :return: board evaluation
        """
        return randint(int(self._loss_value), int(self._win_value))
