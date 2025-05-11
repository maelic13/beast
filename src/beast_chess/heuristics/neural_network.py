from pathlib import Path

import chess
import onnxruntime as ort

from beast_chess.neural_networks import NetInputFactory

from .infra import Heuristic


class NeuralNetwork(Heuristic):
    """Old neural network versions for Beast versions <2.0."""

    def __init__(
        self,
        model_file: Path,
        fifty_moves_rule: bool = True,  # noqa: FBT001, FBT002
        syzygy_path: str | None = None,
        syzygy_probe_limit: int = 7,
    ) -> None:
        """
        Constructor.
        :param model_file: the path to a neural network file
        :param fifty_moves_rule: should enforce the 50-move rule
        :param syzygy_path: path to syzygy tablebases
        :param syzygy_probe_limit: limit for the maximum number of pieces in the tablebases
        """
        super().__init__(fifty_moves_rule, syzygy_path, syzygy_probe_limit)
        self._session = ort.InferenceSession(model_file)
        self._nn_input = NetInputFactory.from_string(
            self._session.get_modelmeta().custom_metadata_map.get("model_version")
        )

    def _evaluate_internal(self, board: chess.Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
        output = self._session.run(
            None, {self._session.get_inputs()[0].name: [self._nn_input(board.fen())]}
        )
        return round(output[0][0][0] * 2000)
