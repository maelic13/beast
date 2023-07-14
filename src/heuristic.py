import numpy as np
from random import uniform, randrange

from chess import BISHOP, Board, BLACK, KNIGHT, QUEEN, PAWN, ROOK, SquareSet, WHITE
from chess.syzygy import open_tablebase

from options import Options


# Piece values
PAWN_VALUE = 100
KNIGHT_VALUE = 350
BISHOP_VALUE = 350
ROOK_VALUE = 525
QUEEN_VALUE = 1000

# Parameter weights for bonus eval
PAWN_RANK_WEIGHT = 7
PAWN_FILE_WEIGHT = 5
PAWN_CENTER_WEIGHT = 5
PAWN_DISTANCE_WEIGHT = 5

KNIGHT_CENTER_WEIGHT = 7
KNIGHT_DISTANCE_WEIGHT = 8

BISHOP_CENTER_WEIGHT = 5
BISHOP_DISTANCE_WEIGHT = 8

ROOK_CENTER_WEIGHT = 8
ROOK_DISTANCE_WEIGHT = 5

QUEEN_CENTER_WEIGHT = 2
QUEEN_DISTANCE_WEIGHT = 8

KING_CENTER_WEIGHT = 8
KING_DISTANCE_WEIGHT = 5


def heuristic(fen: str, options: Options) -> int:
    """
    Heuristic for chess engine, returns evaluation based on chosen heuristic stype in options.
    :param fen: board representation in fen format
    :param options: search options
    :return: evaluation
    """
    if options.heuristic == "random":
        return random_evaluation()

    board = Board(fen)
    if board.is_game_over():
        if board.is_checkmate():
            return -25500
        return 0

    if options.fiftyMoveRule and int(fen.split(' ')[4]) >= 100:
        return 0

    # tablebase probing
    evaluation = 0
    if len(board.piece_map()) <= options.syzygyProbeLimit and options.syzygyPath != '<empty>':
        with open_tablebase(options.syzygyPath) as tablebase:
            wdl = tablebase.get_wdl(board)

        if options.fiftyMoveRule and wdl == 2:
            evaluation = 12800
        elif options.fiftyMoveRule and wdl == -2:
            evaluation = -12800
        elif not options.fiftyMoveRule and wdl == 1:
            evaluation = 12800
        elif not options.fiftyMoveRule and wdl == -1:
            evaluation = -12800
        else:
            return 0

    if options.heuristic == "neuralnetwork":
        evaluation += nn_evaluation(board, options)
    else:
        evaluation += classical_evaluation(board)
    return evaluation


def classical_evaluation(board: Board) -> int:
    """
    Classical style heuristic function based on piece values and derived from human knowledge.
    :param board: board representation
    :return: position evaluation
    """
    # pieces
    w_pawns = board.pieces(PAWN, WHITE)
    b_pawns = board.pieces(PAWN, BLACK)
    w_knights = board.pieces(KNIGHT, WHITE)
    b_knights = board.pieces(KNIGHT, BLACK)
    w_bishops = board.pieces(BISHOP, WHITE)
    b_bishops = board.pieces(BISHOP, BLACK)
    w_rooks = board.pieces(ROOK, WHITE)
    b_rooks = board.pieces(ROOK, BLACK)
    w_queens = board.pieces(QUEEN, WHITE)
    b_queens = board.pieces(QUEEN, BLACK)
    w_king = board.king(WHITE)
    b_king = board.king(BLACK)

    # Initial eval - adding value of pieces on board
    evaluation = (len(w_pawns) * PAWN_VALUE - len(b_pawns) * PAWN_VALUE
                  + len(w_knights) * KNIGHT_VALUE - len(b_knights) * KNIGHT_VALUE
                  + len(w_bishops) * BISHOP_VALUE - len(b_bishops) * BISHOP_VALUE
                  + len(w_rooks) * ROOK_VALUE - len(b_rooks) * ROOK_VALUE
                  + len(w_queens) * QUEEN_VALUE - len(b_queens) * QUEEN_VALUE)

    # Pawns
    wp_bonus = pawn_bonus(w_pawns, b_king, True)
    bp_bonus = pawn_bonus(b_pawns, w_king, False)

    # Knights
    wk_bonus = knight_bonus(w_knights, b_king)
    bk_bonus = knight_bonus(b_knights, w_king)

    # Bishops
    wb_bonus = bishop_bonus(w_bishops, b_king)
    bb_bonus = bishop_bonus(b_bishops, w_king)

    # Rooks
    wr_bonus = rook_bonus(w_rooks, b_king)
    br_bonus = rook_bonus(b_rooks, w_king)

    # Queens
    wq_bonus = queen_bonus(w_queens, b_king)
    bq_bonus = queen_bonus(b_queens, w_king)

    # Kings
    wki_bonus = king_bonus(w_king, b_king, bool(b_queens))
    bki_bonus = king_bonus(b_king, w_king, bool(w_queens))

    # Add bonuses to eval
    evaluation += (wp_bonus - bp_bonus + wk_bonus - bk_bonus + wb_bonus - bb_bonus
                   + wr_bonus - br_bonus + wq_bonus - bq_bonus + wki_bonus - bki_bonus)

    # Assign eval to node
    if not board.turn:
        return -int(evaluation)
    return int(evaluation)


def nn_evaluation(board: Board, options: Options) -> int:
    """
    Position evaluation by neural network.
    :param board: board representation
    :param options: search options
    :return: evaluation
    """
    if '3-100k' in options.modelFile:
        data = np.array([fen_to_input(board.fen())])
        evaluation = (options.model.predict_classes(data)[0] - 3) * 100 + randrange(-50, 51, 1)
        return int(evaluation)
    elif options.network == "Classification":
        data = np.array([fen_to_input(board.fen())])
        evaluation = (options.model.predict_classes(data)[0] - 3) * 100 + randrange(-50, 51, 1)
        if board.turn:
            return int(evaluation)
        else:
            return -int(evaluation)
    elif '100k' in options.modelFile:
        data = np.array([fen_to_input(board.fen())])
        evaluation = options.model.predict(data, verbose=0)
        return int(round(evaluation[0][0] * 2000))

    data = np.array([fen_to_input(board.fen())])
    evaluation = options.model.predict(data, verbose=0)
    if board.turn:
        return int(round(evaluation[0][0] * 2000))
    return -int(round(evaluation[0][0] * 2000))


def random_evaluation():
    """
    Give random evaluation to the position.
    :return: random integer
    """
    return int(uniform(0, 2000))


def occupying_center_bonus(piece_position: int, bonus: int) -> int:
    """
    Bonus for occupying squares close to center.
    :param piece_position: position of piece to evaluate
    :param bonus: bonus value for piece type
    :return: evaluation bonus
    """
    if (int(piece_position / 8) in range(3, 5) and piece_position % 8 in range(3, 5)
            or int(piece_position / 8) in range(2, 6) and piece_position % 8 in range(2, 6)
            or int(piece_position / 8) in range(1, 7) and piece_position % 8 in range(1, 7)):
        return bonus
    return 0


def distance_from_king_bonus(piece_position: int, king_position: int, bonus: int) -> int:
    """
    Bonus for distance from opponent's king.
    :param piece_position: position of piece to evaluate
    :param king_position: opponent king's position
    :param bonus: bonus value for piece type
    :return: evaluation bonus
    """
    distance = (abs(int(piece_position / 8) - int(king_position / 8))
                + abs(piece_position % 8 - king_position % 8))
    return int(14 / distance * bonus - bonus)


def pawn_bonus(pawns: SquareSet, king_position: int, color: bool) -> int:
    """
    Evaluation bonus for positions of pawns on board.
    :param pawns: set of squares containing pawns
    :param king_position: opponent king's position on board
    :param color: player to move, white True, black False
    :return: evaluation bonus
    """
    p_bonus = 0
    for pawn_position in pawns:
        # rank bonus -> the further forward the pawn, the more of a bonus
        if color:
            p_bonus += (int(pawn_position / 8) - 1) * PAWN_RANK_WEIGHT
        else:
            p_bonus += (6 - int(pawn_position / 8)) * PAWN_RANK_WEIGHT

        # file penalty -> central files take none, the closer to rim the less pawn's value
        if pawn_position % 8 < 3:
            p_bonus -= (3 - pawn_position % 8) * PAWN_FILE_WEIGHT
        elif pawn_position % 8 > 4:
            p_bonus -= (pawn_position % 8 - 4) * PAWN_FILE_WEIGHT

        # occupying center bonus
        p_bonus += occupying_center_bonus(pawn_position, PAWN_CENTER_WEIGHT)
        # distance from king bonus
        p_bonus += distance_from_king_bonus(pawn_position, king_position, PAWN_DISTANCE_WEIGHT)

    return p_bonus


def knight_bonus(knights: SquareSet, king_position: int) -> int:
    """
    Evaluation bonus for positions knights on board.
    :param knights: set of squares containing knights
    :param king_position: opponent king's position on board
    :return: evaluation bonus
    """
    k_bonus = 0
    for knight_position in knights:
        # occupying center bonus
        k_bonus += occupying_center_bonus(knight_position, KNIGHT_CENTER_WEIGHT)

        # distance from king bonus
        k_bonus += distance_from_king_bonus(knight_position, king_position, KNIGHT_DISTANCE_WEIGHT)

    return k_bonus


def bishop_bonus(bishops: SquareSet, king_position: int) -> int:
    """
    Evaluation bonus for positions of bishops on board.
    :param bishops: set of squares containing bishops
    :param king_position: opponent king's position on board
    :return: evaluation bonus
    """
    b_bonus = 0
    for bishop_position in bishops:
        # occupying center bonus
        b_bonus += occupying_center_bonus(bishop_position, BISHOP_CENTER_WEIGHT)

        # distance from king bonus
        b_bonus += distance_from_king_bonus(bishop_position, king_position, KNIGHT_DISTANCE_WEIGHT)

    return b_bonus


def rook_bonus(rooks: SquareSet, king_position: int) -> int:
    """
    Evaluation bonus for positions of rooks on board.
    :param rooks: set of squares containing rooks
    :param king_position: opponent king's position on board
    :return: evaluation bonus
    """
    r_bonus = 0
    for rook_position in rooks:
        # occupying center files bonus
        if rook_position % 8 in range(3, 5):
            r_bonus += ROOK_CENTER_WEIGHT
        if rook_position % 8 in range(2, 6):
            r_bonus += ROOK_CENTER_WEIGHT
        if rook_position % 8 in range(1, 7):
            r_bonus += ROOK_CENTER_WEIGHT

        # distance from king bonus
        r_bonus += distance_from_king_bonus(rook_position, king_position, ROOK_DISTANCE_WEIGHT)

    return r_bonus


def queen_bonus(queens: SquareSet, king_position: int) -> int:
    """
    Evaluation bonus for positions of queens on board.
    :param queens: set of squares containing queens
    :param king_position: opponent king's position on board
    :return: evaluation bonus
    """
    q_bonus = 0
    for queen_position in queens:
        # occupying center bonus
        q_bonus += occupying_center_bonus(queen_position, QUEEN_CENTER_WEIGHT)

        # distance from king bonus
        q_bonus += distance_from_king_bonus(queen_position, king_position, QUEEN_DISTANCE_WEIGHT)

    return q_bonus


def king_bonus(king_position: int, opponents_king: int, no_queen: bool) -> int:
    """
    Evaluation bonus for positions of king on board.
    :param king_position: king's position on board
    :param opponents_king: opponent king's position on board
    :param no_queen: information about presence of opponent's queens on board
    :return: evaluation bonus
    """
    k_bonus = 0
    if no_queen:
        king_center_weight = KING_CENTER_WEIGHT
    else:
        king_center_weight = -KING_CENTER_WEIGHT

    # occupying center bonus
    k_bonus += occupying_center_bonus(king_position, king_center_weight)

    # distance from king bonus
    k_bonus += distance_from_king_bonus(king_position, opponents_king, KING_DISTANCE_WEIGHT)

    return k_bonus


def fen_to_input(fen: str) -> np.ndarray:
    """
    Convert board representation in fen format to input for neural network.
    :param fen: board representation
    :return: input for neural network
    """
    fen = fen.split(' ')
    inp = np.zeros((7, 8, 8), dtype=int)

    # plane who's to move
    if fen[1] == 'w':
        inp[6, ] = np.ones((8, 8), dtype=int)
    else:
        inp[6, ] = -np.ones((8, 8), dtype=int)

    # parse board
    fen = fen[0].split('/')
    row = 0
    for each in fen:
        col = 0
        for sign in each:
            if sign == 'p':
                inp[0, row, col] = -1
            elif sign == 'P':
                inp[0, row, col] = 1
            elif sign == 'n':
                inp[1, row, col] = -1
            elif sign == 'N':
                inp[1, row, col] = 1
            elif sign == 'b':
                inp[2, row, col] = -1
            elif sign == 'B':
                inp[2, row, col] = 1
            elif sign == 'r':
                inp[3, row, col] = -1
            elif sign == 'R':
                inp[3, row, col] = 1
            elif sign == 'q':
                inp[4, row, col] = -1
            elif sign == 'Q':
                inp[4, row, col] = 1
            elif sign == 'k':
                inp[5, row, col] = -1
            elif sign == 'K':
                inp[5, row, col] = 1
            else:
                col += int(sign) - 1
            col += 1
        row += 1

    return inp
