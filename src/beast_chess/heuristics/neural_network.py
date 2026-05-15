from pathlib import Path

import onnxruntime as ort

from beast_chess.board import Board
from beast_chess.neural_networks import NetInputFactory

from .infra import Heuristic


class NeuralNetwork(Heuristic):
    def __init__(
        self,
        model_file: Path,
        threads: int = 1,
    ) -> None:
        """
        Constructor.
        :param model_file: the path to a neural network file
        """
        super().__init__()

        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        self._session = ort.InferenceSession(model_file, options)

        self._nn_input = NetInputFactory.from_string(
            self._session.get_modelmeta().custom_metadata_map.get("model_version")
        )

    def _evaluate_internal(self, board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
        output = self._session.run(
            None, {self._session.get_inputs()[0].name: [self._nn_input(board.fen())]}
        )
        return round(output[0][0][0] * 2000)
