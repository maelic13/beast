from collections.abc import Iterable
from multiprocessing import cpu_count, Pool
from pathlib import Path
from time import time

from chess import BISHOP, Board, KING, KNIGHT, PAWN, QUEEN, ROOK
import numpy as np

from tensorflow.keras import Sequential
from tensorflow.keras.activations import relu, sigmoid
from tensorflow.keras.callbacks import EarlyStopping, History
from tensorflow.keras.layers import (
    Activation, BatchNormalization, Conv2D, Dense, Dropout, Flatten)
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.metrics import BinaryAccuracy
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam

from .pgn_convert import DataHelper


class BeastNeuralNetwork:
    """ Neural network for Beast chess engine. """
    def __init__(self) -> None:
        self.history: History | None = None
        self.model: Sequential = self._initialize_model()

    def evaluate(self, fen: str) -> float:
        """
        Evaluate position in FEN format and return win probability for side to move.
        :param fen: board representation in FEN format
        :return: win probability (0.0 to 1.0)
        """
        return self.model.predict(np.array([self.fen_to_input(fen)]), verbose=0)[0][0]

    def train_model(self, x_train: np.ndarray, x_test: np.ndarray, y_train: np.ndarray,
                    y_test: np.ndarray) -> None:
        """
        Train Beast neural network.
        :param x_train: x data for training
        :param x_test: x data for testing
        :param y_train: y data for training
        :param y_test: y data for testing
        """
        self.history = self.model.fit(
            x_train,
            y_train,
            batch_size=256,
            epochs=512,
            validation_data=(x_test, y_test),
            callbacks=[EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=8)]
        )

    def load_model(self, path: Path | str) -> None:
        """
        Load already trained model from file.
        :param path: path to model file
        """
        self.model = load_model(path)

    @classmethod
    def convert_fen_positions_to_input_structures(
            cls, fens: list[str], num_processes: int | None = None) -> list[np.ndarray]:
        """
        Convert iterable of FEN strings to list of input structures for neural network training.
        :param fens: positions in FEN format
        :param num_processes: number of processes (and therefore cpus) to use for conversion
        :return: positions in input format for neural network training
        """
        start = time()
        print("Converting FEN positions to inputs...")

        num_processes = num_processes or cpu_count()
        input_positions: list[np.ndarray] = []
        fens = DataHelper.parse_data(fens, num_processes)

        with Pool(processes=num_processes) as pool:
            for sub_result in pool.map(cls.fens_to_inputs, fens):
                input_positions += sub_result

        print(f"Inputs created in {int(time() - start)} seconds.\n")
        return input_positions

    @classmethod
    def fens_to_inputs(cls, fens: list[str]) -> list[np.ndarray]:
        """
        Convert list of positions in FEN notations to input structures. To be used
        with multiprocessing.Pool for faster conversion.
        :param fens:
        :return:
        """
        converted: list[np.ndarray] = []
        for fen in fens:
            converted.append(cls.fen_to_input(fen))
        return converted

    @staticmethod
    def fen_to_input(fen: str) -> np.ndarray:
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

    def evaluate_model(self, x_test: Iterable[np.ndarray], y_test: Iterable[np.ndarray]) -> None:
        """
        Test model and print scores.
        :param x_test: x data to evaluate model
        :param y_test: y data to evaluate model
        """
        score, acc = self.model.evaluate(x_test, y_test, batch_size=128)
        print(f"Test score: {score}")
        print(f"Test accuracy: {acc}")

    def save_model(self, folder_path: str, name: str) -> None:
        """
        Save trained model in *.keras format.
        :param folder_path: path to target folder
        :param name: name of the model
        """
        self.model.save(f"{folder_path}/{name}.keras")

    @staticmethod
    def _initialize_model() -> Sequential:
        """
        Create and compile model structure.
        :return: model structure
        """
        model = Sequential()
        model.add(Conv2D(128, kernel_size=3, input_shape=(6, 8, 8)))
        model.add(BatchNormalization())
        model.add(Activation(relu))

        model.add(Conv2D(128, kernel_size=3))
        model.add(BatchNormalization())
        model.add(Activation(relu))

        model.add(Flatten())

        model.add(Dense(256))
        model.add(Activation(relu))
        model.add(Dropout(0.2))

        model.add(Dense(1))
        model.add(Activation(sigmoid))

        model.compile(
            loss=BinaryCrossentropy(),
            optimizer=Adam(learning_rate=0.001),
            metrics=[BinaryAccuracy()]
        )
        return model
