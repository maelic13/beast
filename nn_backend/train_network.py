from collections.abc import Iterable
from os import environ
from time import time
from typing import Any

from chess import BISHOP, Board, KING, KNIGHT, PAWN, QUEEN, ROOK
import numpy as np

from sklearn.model_selection import train_test_split
from tensorflow.keras import Sequential
from tensorflow.keras.activations import relu, sigmoid
from tensorflow.keras.callbacks import EarlyStopping, History
from tensorflow.keras.layers import (
    Activation, BatchNormalization, Conv2D, Dense, Dropout, Flatten)
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.metrics import BinaryAccuracy
from tensorflow.keras.optimizers import Adam


class ModelTrainer:
    @staticmethod
    def load_txt_data(path_to_file: str) -> tuple[list[str], list[float]]:
        """
        Load data from txt file and parse them into list of positions in FEN format
        and list of evaluations in WDL format (chance of victory for side to move, 0.0 - 1.0).
        :param path_to_file: txt file containing positions and evaluations from pgn_convert script
        :return: list of positions in FEN format and list of evaluations in WDL format
        """
        start = time()
        print("Loading txt data...")
        with open(path_to_file, 'r') as file:
            lines = file.readlines()

        fens: list[str] = []
        evals: list[float] = []
        for line in lines:
            temp = line.strip().split('\t')
            fens.append(temp[0])
            evals.append(float(temp[1]))

        print(f"Data loaded in {time() - start} seconds.\n")
        return fens, evals

    @staticmethod
    def load_numpy_data(path_to_folder: str) -> tuple[np.ndarray, np.ndarray]:
        return np.load(path_to_folder + "/inputs.npy"), np.load(path_to_folder + "/outputs.npy")

    @staticmethod
    def save_numpy_data(path_to_folder: str, inputs: Iterable[Any], outputs: Iterable[Any]) -> None:
        """
        Save already processed data for neural network training in numpy format for fast loading.
        :param path_to_folder: path to folder for inputs.npy and outputs.npy files
        :param inputs: processed input positions
        :param outputs: processed output evaluations
        """
        np.save(path_to_folder + "/inputs.npy", inputs)
        np.save(path_to_folder + "/outputs.npy", outputs)

    @classmethod
    def train_ffnn(cls, x_train, x_test, y_train, y_test) -> tuple[Sequential, History]:
        model = Sequential()
        model.add(Conv2D(128, kernel_size=3, input_shape=x_train[0].shape))
        model.add(BatchNormalization())
        model.add(Activation(relu))

        model.add(Conv2D(256, kernel_size=3))
        model.add(BatchNormalization())
        model.add(Activation(relu))

        model.add(Flatten())

        model.add(Dense(256))
        model.add(Activation(relu))
        model.add(Dropout(0.5))

        model.add(Dense(1))
        model.add(Activation(sigmoid))

        model.compile(
            loss=BinaryCrossentropy(),
            optimizer=Adam(learning_rate=0.0001),
            metrics=[BinaryAccuracy()]
        )

        history = model.fit(
            x_train,
            y_train,
            batch_size=256,
            epochs=128,
            validation_data=(x_test, y_test),
            callbacks=[EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=8)]
        )

        return model, history

    @staticmethod
    def eval_model(model: Sequential, x_test: Iterable[np.ndarray], y_test: Iterable[np.ndarray]):
        # Test model and print score
        model.save("model.keras")
        score, acc = model.evaluate(x_test, y_test, batch_size=128)
        print(f"Test score: {score}")
        print(f"Test accuracy: {acc}")

    @classmethod
    def convert_fen_positions_to_input_structures(cls, fens: Iterable[str]) -> list[np.ndarray]:
        """
        Convert iterable of FEN strings to list of input structures for neural network training.
        :param fens: positions in FEN format
        :return: positions in input format for neural network training
        """
        start = time()
        print("Converting FEN positions to inputs...")
        input_positions: list[np.ndarray] = []
        for fen in fens:
            input_positions.append(cls.fen_to_input(fen))
        print(f"Inputs created in {time() - start} seconds.\n")
        return input_positions

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


if __name__ == "__main__":
    environ["TF_CPP_MIN_LOG_LEVEL"] = "1"

    # load data from txt file, conversion needed (long)
    # positions, evaluations = ModelTrainer.load_txt_data("../data/evaluated_positions.txt")
    # positions = ModelTrainer.convert_fen_positions_to_input_structures(positions)

    # save numpy data (overwrite)
    # ModelTrainer.save_numpy_data(".", positions, evaluations)

    # load data from numpy file (fast)
    positions, evaluations = ModelTrainer.load_numpy_data(".")

    x_tr, x_te, y_tr, y_te = train_test_split(
        positions, evaluations, test_size=0.2, random_state=42)

    trained_model, _ = ModelTrainer.train_ffnn(x_tr, x_te, y_tr, y_te)
    ModelTrainer.eval_model(trained_model, x_te, y_te)
