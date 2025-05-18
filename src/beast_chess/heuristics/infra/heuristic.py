from abc import ABC, abstractmethod
from math import log10

from chess import Board
from chess.syzygy import open_tablebase


class Heuristic(ABC):
    def __init__(
        self,
        fifty_moves_rule: bool = True,  # noqa: FBT001, FBT002
        syzygy_path: str | None = None,
        syzygy_probe_limit: int = 7,
    ) -> None:
        """
        Common constructor for heuristics.
        :param fifty_moves_rule: should enforce 50 move rule
        :param syzygy_path: path to syzygy tablebases
        :param syzygy_probe_limit: limit for the maximum number of pieces in the tablebases
        """
        self.fifty_moves_rule = fifty_moves_rule
        self._syzygy_path = syzygy_path
        self._syzygy_probe_limit = syzygy_probe_limit

        # precalculate win and loss values (speed-up of heuristic)
        self.draw_value = self.probability_to_centipawn(0.5) * 100  # [cp]
        self.loss_value = self.probability_to_centipawn(0.0) * 100  # [cp]
        self.win_value = self.probability_to_centipawn(1.0) * 100  # [cp]

    def evaluate_result(self, board: Board, depth: int) -> float:
        if board.outcome().winner is None:
            return self.draw_value

        if board.turn is not board.outcome().winner:
            return self.loss_value - 100 * depth

        return self.win_value + 100 * depth

    def evaluate_position(self, board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
        if board.is_game_over():
            if board.is_checkmate():
                return self.loss_value
            return self.draw_value

        # tablebase probing
        tablebase_evaluation = 0.0
        if len(board.piece_map()) <= self._syzygy_probe_limit and self._syzygy_path is not None:
            with open_tablebase(self._syzygy_path) as tablebase:
                wdl = tablebase.get_wdl(board)

            if (self.fifty_moves_rule and wdl == 2) or (not self.fifty_moves_rule and wdl == 1):
                tablebase_evaluation = self.win_value
            elif (self.fifty_moves_rule and wdl == -2) or (not self.fifty_moves_rule and wdl == -1):
                tablebase_evaluation = self.loss_value
            else:
                return self.draw_value

        return tablebase_evaluation + self._evaluate_internal(board)

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
