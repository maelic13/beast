import chess
import numpy as np

PIECE_TO_PLANE = {
    (chess.WHITE, chess.PAWN): 0,
    (chess.WHITE, chess.KNIGHT): 1,
    (chess.WHITE, chess.BISHOP): 2,
    (chess.WHITE, chess.ROOK): 3,
    (chess.WHITE, chess.QUEEN): 4,
    (chess.WHITE, chess.KING): 5,
    (chess.BLACK, chess.PAWN): 6,
    (chess.BLACK, chess.KNIGHT): 7,
    (chess.BLACK, chess.BISHOP): 8,
    (chess.BLACK, chess.ROOK): 9,
    (chess.BLACK, chess.QUEEN): 10,
    (chess.BLACK, chess.KING): 11,
}


def board_to_input(board: chess.Board) -> np.ndarray:
    """
    Convert board representation to input for the v2 neural network.
    :param board: chess board representation
    :return: input for neural network
    """
    arr = np.zeros((17, 8, 8), dtype=np.float32)

    for square, piece in board.piece_map().items():
        row = 7 - chess.square_rank(square)
        col = chess.square_file(square)
        arr[PIECE_TO_PLANE[(piece.color, piece.piece_type)], row, col] = 1.0

    arr[12].fill(1.0 if board.turn == chess.WHITE else 0.0)
    arr[13].fill(1.0 if board.has_kingside_castling_rights(chess.WHITE) else 0.0)
    arr[14].fill(1.0 if board.has_queenside_castling_rights(chess.WHITE) else 0.0)
    arr[15].fill(1.0 if board.has_kingside_castling_rights(chess.BLACK) else 0.0)
    arr[16].fill(1.0 if board.has_queenside_castling_rights(chess.BLACK) else 0.0)
    return arr


def fen_to_input(fen: str) -> np.ndarray:
    """
    Backward-compatible FEN conversion wrapper.
    :param fen: board representation
    :return: input for neural network
    """
    return board_to_input(chess.Board(fen))
