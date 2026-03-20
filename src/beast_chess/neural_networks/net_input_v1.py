import chess
import numpy as np

PIECE_TO_PLANE = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 2,
    chess.ROOK: 3,
    chess.QUEEN: 4,
    chess.KING: 5,
}


def board_to_input(board: chess.Board) -> np.ndarray:
    """
    Convert board representation to input for the v1 neural network.
    :param board: chess board representation
    :return: input for neural network
    """
    inp = np.zeros((7, 8, 8), dtype=np.float32)
    inp[6].fill(1.0 if board.turn == chess.WHITE else -1.0)

    for square, piece in board.piece_map().items():
        row = 7 - chess.square_rank(square)
        col = chess.square_file(square)
        inp[PIECE_TO_PLANE[piece.piece_type], row, col] = 1.0 if piece.color else -1.0

    return inp


def fen_to_input(fen: str) -> np.ndarray:
    """
    Backward-compatible FEN conversion wrapper.
    :param fen: board representation
    :return: input for neural network
    """
    return board_to_input(chess.Board(fen))
