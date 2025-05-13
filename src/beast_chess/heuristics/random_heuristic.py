from random import randint

from chess import Board

from .infra import Heuristic


class RandomHeuristic(Heuristic):
    """Random heuristic."""

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
        return randint(int(self.loss_value), int(self.win_value))
