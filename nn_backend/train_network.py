from collections.abc import Iterable
from os import environ
from time import time
from typing import Any

import numpy as np

from sklearn.model_selection import train_test_split

from beast_neural_network import BeastNeuralNetwork


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

        print(f"Data loaded in {int(time() - start)} seconds.\n")
        return fens, evals

    @staticmethod
    def load_numpy_data(path_to_folder: str, name: str) -> tuple[np.ndarray, np.ndarray]:
        return (np.load(path_to_folder + f"/{name}_inputs.npy"),
                np.load(path_to_folder + f"/{name}_outputs.npy"))

    @staticmethod
    def save_numpy_data(path_to_folder: str, name: str, inputs: Iterable[Any],
                        outputs: Iterable[Any]) -> None:
        """
        Save already processed data for neural network training in numpy format for fast loading.
        :param path_to_folder: path to folder for inputs.npy and outputs.npy files
        :param name: prefix for name of the files
        :param inputs: processed input positions
        :param outputs: processed output evaluations
        """
        np.save(path_to_folder + f"/{name}_inputs.npy", inputs)
        np.save(path_to_folder + f"/{name}_outputs.npy", outputs)


if __name__ == "__main__":
    environ["TF_CPP_MIN_LOG_LEVEL"] = "1"
    beast_neural_network = BeastNeuralNetwork()

    # load data from txt file, conversion needed (long)
    positions, evaluations = ModelTrainer.load_txt_data("games.txt")
    positions = beast_neural_network.convert_fen_positions_to_input_structures(positions)

    # save numpy data (overwrite)
    ModelTrainer.save_numpy_data(".", "games", positions, evaluations)

    # load data from numpy file (fast)
    positions, evaluations = ModelTrainer.load_numpy_data(".", "games")

    x_tr, x_te, y_tr, y_te = train_test_split(
        positions, evaluations, test_size=0.2, random_state=42)

    beast_neural_network.train_model(x_tr, x_te, y_tr, y_te)
    beast_neural_network.evaluate_model(x_te, y_te)
    beast_neural_network.save_model(".", "games")
