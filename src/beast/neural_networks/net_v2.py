import numpy as np

from .net import Net


class NetV2(Net):
    @staticmethod
    def fen_to_input(fen: str) -> np.ndarray:
        raise NotImplementedError
