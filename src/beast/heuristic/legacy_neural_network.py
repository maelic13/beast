from pathlib import Path

import chess
import numpy as np
import onnxruntime as ort

from .heuristic import Heuristic


class LegacyNeuralNetwork(Heuristic):
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
        self._model_name = model_file.name

    @staticmethod
    def use_quiescence() -> bool:
        """
        Whether to use quiescence search with this heuristic.
        :return: use quiescence or not
        """
        return True

    def _evaluate_internal(self, board: chess.Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
        output = self._session.run(
            None, {self._session.get_inputs()[0].name: [self._fen_to_input(board.fen())]}
        )
        return round(output[0][0][0] * 2000)

    @staticmethod
    def _fen_to_input(fen: str) -> np.ndarray:  # noqa: C901, PLR0912
        """
        Convert board representation in fen format to input for neural network.
        :param fen: board representation
        :return: input for neural network
        """
        fen = fen.split(" ")
        inp = np.zeros((7, 8, 8), dtype=np.float32)

        # plane who's to move
        if fen[1] == "w":
            inp[6,] = np.ones((8, 8), dtype=np.float32)
        else:
            inp[6,] = -np.ones((8, 8), dtype=np.float32)

        # parse board
        fen = fen[0].split("/")
        for row, each in enumerate(fen):
            col = 0
            for sign in each:
                if sign == "p":
                    inp[0, row, col] = -1
                elif sign == "P":
                    inp[0, row, col] = 1
                elif sign == "n":
                    inp[1, row, col] = -1
                elif sign == "N":
                    inp[1, row, col] = 1
                elif sign == "b":
                    inp[2, row, col] = -1
                elif sign == "B":
                    inp[2, row, col] = 1
                elif sign == "r":
                    inp[3, row, col] = -1
                elif sign == "R":
                    inp[3, row, col] = 1
                elif sign == "q":
                    inp[4, row, col] = -1
                elif sign == "Q":
                    inp[4, row, col] = 1
                elif sign == "k":
                    inp[5, row, col] = -1
                elif sign == "K":
                    inp[5, row, col] = 1
                else:
                    col += int(sign) - 1
                col += 1

        return inp
