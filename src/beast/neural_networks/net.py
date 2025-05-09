from abc import ABC, abstractmethod

import numpy as np


class Net(ABC):
    @staticmethod
    @abstractmethod
    def fen_to_input(fen: str) -> np.ndarray:
        """
        Convert board representation in fen format to input for neural network.
        :param fen: board representation
        :return: input for neural network
        """
