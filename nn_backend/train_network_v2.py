from random import sample, seed
from time import time
from typing import List, Optional, Tuple

from tensorflow.python.keras import Sequential
from sklearn.model_selection import train_test_split


class ModelTrainer:
    @staticmethod
    def load_data(path_to_file: str, num_data: Optional[int] = None, random: bool = False,
                  random_seed: int = 1) -> Tuple[List[str], List[float]]:
        with open(path_to_file) as file:
            data = file.read().splitlines()

        if random and num_data:
            seed(random_seed)
            data = sample(data, num_data)

        if not random and num_data:
            data = data[:num_data]

        return [x.split("\t")[0] for x in data], [float(x.split("\t")[1]) for x in data]

    @classmethod
    def train_ffnn(cls, x_train, x_test, y_train, y_test) -> Sequential:
        model = Sequential()
        return model


if __name__ == "__main__":
    start = time()
    positions, evaluations = ModelTrainer.load_data("evaluated_games.txt")
    print(f"{len(positions)} data loaded in {round(time() - start, 2)} seconds.")
    X_train, X_test, Y_train, Y_test = train_test_split(
        positions, evaluations, test_size=0.2, random_state=42)

    trained_model = ModelTrainer.train_ffnn(X_train, X_test, Y_train, Y_test)
