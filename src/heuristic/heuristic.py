from abc import ABC, abstractmethod
from math import log10

from chess import Board
from chess.syzygy import open_tablebase


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

        # precalculate win and loss values (speed-up of heuristic)
        self._draw_value = self.win_probability_to_pawn_advantage(0.5) * 100  # [cp]
        self._loss_value = self.win_probability_to_pawn_advantage(0.) * 100  # [cp]
        self._win_value = self.win_probability_to_pawn_advantage(1.) * 100  # [cp]

    @staticmethod
    @abstractmethod
    def use_quiescence() -> bool:
        """
        Whether to use quiescence search with this heuristic.
        :return: use quiescence or not
        """

    def evaluate(self, board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
        if board.is_game_over():
            if board.is_checkmate():
                return self._loss_value
            return self._draw_value

        if (self._fifty_moves_rule and board.can_claim_fifty_moves()
                or board.can_claim_threefold_repetition()):
            return self._draw_value

        # tablebase probing
        tablebase_evaluation = 0.
        if len(board.piece_map()) <= self._syzygy_probe_limit and self._syzygy_path is not None:
            with open_tablebase(self._syzygy_path) as tablebase:
                wdl = tablebase.get_wdl(board)

            if self._fifty_moves_rule and wdl == 2 or not self._fifty_moves_rule and wdl == 1:
                tablebase_evaluation = self._win_value
            elif self._fifty_moves_rule and wdl == -2 or not self._fifty_moves_rule and wdl == -1:
                tablebase_evaluation = self._loss_value
            else:
                return self._draw_value

        return int(tablebase_evaluation + self._evaluate_internal(board))

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
        if win_probability <= 0:
            win_probability = 1e-9
        elif win_probability >= 1:
            win_probability = 1. - 1e-9
        return 4 * log10(win_probability / (1 - win_probability))

    @abstractmethod
    def _evaluate_internal(self, board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
