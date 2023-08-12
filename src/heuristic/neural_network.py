from pathlib import Path

from chess import BISHOP, Board, KING, KNIGHT, PAWN, QUEEN, ROOK
import numpy as np
from tensorflow.keras.models import load_model

from .heuristic import Heuristic


# TODO: Solve duplication of evaluation code from BeastNeuralNetwork!


class NeuralNetwork(Heuristic):
    """ Neural network versions for Beast versions 2.0+. """
    def __init__(self, model_file: Path, fifty_moves_rule: bool = True,
                 syzygy_path: str | None = None, syzygy_probe_limit: int = 7) -> None:
        """
        Constructor.
        :param model_file: path to neural network file
        :param fifty_moves_rule: should enforce 50 move rule
        :param syzygy_path: path to syzygy tablebases
        :param syzygy_probe_limit: limit for maximum number of pieces the tablebases can be used for
        """
        super().__init__(fifty_moves_rule, syzygy_path, syzygy_probe_limit)
        self._model = load_model(model_file)

    @staticmethod
    def use_quiescence() -> bool:
        """
        Whether to use quiescence search with this heuristic.
        :return: use quiescence or not
        """
        return False

    def _evaluate_internal(self, board: Board) -> float:
        """
        Evaluate board and return value in centi-pawns.
        :param board: chess board representation
        :return: board evaluation
        """
        evaluation = self._model.predict(
            np.array([self._fen_to_input(board.fen())]), verbose=0)[0][0]
        return self.win_probability_to_pawn_advantage(evaluation) * 100

    @staticmethod
    def _fen_to_input(fen: str) -> np.ndarray:
        """
        Convert board position in FEN notation to input structure for neural network training.
        :param fen: string representing board position
        :return: (6, 8, 8) shape numpy array with each layer representing 1 chess piece type
            in order [pawn, knight, bishop, rook, queen, king]. Each piece type layer is (8, 8)
            shaped representing chess board with 1 in square of own piece of the type
            and -1 in square of opponents piece.
        """
        board = Board(fen)
        return np.asarray([
            np.reshape(
                np.asarray(board.pieces(piece_type, board.turn).tolist(), int)
                - np.asarray(board.pieces(piece_type, not board.turn).tolist(), int),
                (8, 8))
            for piece_type in [PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING]])
