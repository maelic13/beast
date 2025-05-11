import numpy as np


def fen_to_input(fen: str) -> np.ndarray:  # noqa: C901, PLR0912
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
