import numpy as np


def fen_to_input(fen: str) -> np.ndarray:
    """
    Convert a FEN string into a numpy array of shape (17, 8, 8):
    12 piece planes, side-to-move plane, and 4 castling rights planes.
    """
    parts = fen.split()
    rows = parts[0].split("/")
    arr = np.zeros((17, 8, 8), dtype=np.float32)
    piece_map = {
        "P": 0,
        "N": 1,
        "B": 2,
        "R": 3,
        "Q": 4,
        "K": 5,
        "p": 6,
        "n": 7,
        "b": 8,
        "r": 9,
        "q": 10,
        "k": 11,
    }
    for rank_idx, row in enumerate(rows):
        file_idx = 0
        for c in row:
            if c.isdigit():
                file_idx += int(c)
            else:
                arr[piece_map[c], rank_idx, file_idx] = 1.0
                file_idx += 1
    # side to move
    arr[12].fill(1.0 if parts[1] == "w" else 0.0)
    # castling rights
    castling = parts[2] if len(parts) > 2 else "-"
    arr[13].fill(1.0 if "K" in castling else 0.0)
    arr[14].fill(1.0 if "Q" in castling else 0.0)
    arr[15].fill(1.0 if "k" in castling else 0.0)
    arr[16].fill(1.0 if "q" in castling else 0.0)
    return arr
