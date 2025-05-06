from pathlib import Path

import numpy as np
import onnxruntime as ort
from chess import Board

from beast.heuristic.heuristic import Heuristic


class NeuralNetwork(Heuristic):
    """Neural network versions for Beast versions 2.0+."""

    def __init__(
        self,
        model_file: Path,
        fifty_moves_rule: bool = True,  # noqa: FBT001, FBT002
        syzygy_path: str | None = None,
        syzygy_probe_limit: int = 7,
    ) -> None:
        """
        Constructor.
        :param model_file: path to a neural network file
        :param fifty_moves_rule: should enforce 50 move rule
        :param syzygy_path: path to syzygy tablebases
        :param syzygy_probe_limit: limit for the maximum number of pieces in the tablebases
        """
        super().__init__(fifty_moves_rule, syzygy_path, syzygy_probe_limit)
        self._session = ort.InferenceSession(model_file)

    @staticmethod
    def use_quiescence() -> bool:
        """
        Whether to use quiescence search with this heuristic.
        :return: use quiescence or not
        """
        return False

    def _evaluate_internal(self, _board: Board) -> float:  # noqa: PLR6301
        """
        Evaluate board and return value in centi-pawns.
        :param _board: chess board representation
        :return: NotImplemented
        """
        return NotImplemented("New neural network implementation is not yet finished.")

    @staticmethod
    def _fen_to_input(_fen: str) -> np.ndarray:
        """
        Convert board position in FEN notation to input structure for neural network training.
        :param _fen: string representing board position
        :return: NotImplementedError
        """
        return NotImplemented("New neural network implementation is not yet finished.")
