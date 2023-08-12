from abc import ABC, abstractmethod
from math import log10

from chess import Board


class Heuristic(ABC):
    def __init__(self, fifty_moves_rule: bool = True, syzygy_path: str | None = None,
                 syzygy_probe_limit: int = 7) -> None:
        """
        Common constructor for heuristics.
        :param fifty_moves_rule: should enforce 50 move rule
        :param syzygy_path: path to syzygy tablebases
        :param syzygy_probe_limit: limit for maximum number of pieces the tablebases can be used for
        """
        self._fifty_moves_rule = fifty_moves_rule
        self._syzygy_path = syzygy_path
        self._syzygy_probe_limit = syzygy_probe_limit

    @abstractmethod
    def evaluate(self, board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """

    @staticmethod
    @abstractmethod
    def use_quiescence() -> bool:
        """
        Whether to use quiescence search with this heuristic.
        :return: use quiescence or not
        """

    @staticmethod
    def pawn_advantage_to_win_probability(pawn_advantage: float) -> float:
        """
        Calculate winning probability given pawn advantage.
        :param pawn_advantage: advantage in pawns
        :return: winning probability
        """
        return 1 / (1 + 10 ** (-pawn_advantage / 4))

    @staticmethod
    def win_probability_to_pawn_advantage(win_probability: float) -> float:
        """
        Calculate pawn advantage given winning probability.
        :param win_probability: win probability (0.0 to 1.0)
        :return: advantage in pawns
        """
        return 4 * log10(win_probability / (1 - win_probability))
