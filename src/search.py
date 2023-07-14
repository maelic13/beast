import time

from chess import BISHOP, Board, KNIGHT, QUEEN, PAWN, PieceType, ROOK
from keras.backend import clear_session
from keras.models import load_model
from threading import Event, Timer

from go_parameters import GoParameters
from heuristic import BISHOP_VALUE, heuristic, KNIGHT_VALUE, PAWN_VALUE, QUEEN_VALUE, ROOK_VALUE
from node import Node
from options import Options
from timemanagement import get_time_for_move


def main(go_params: GoParameters, options: Options) -> None:
    """
    Main search function, decides options and parameters. Print to console results for GUI to parse.
    :param go_params: search parameters
    :param options: search options
    """
    # initialize values
    root = go_params.root
    depth = 0
    if root.position.split(' ')[1] == 'w':
        root_turn = True
    else:
        root_turn = False

    # time management + timer
    start = time.time()
    time_for_move = get_time_for_move(go_params, options, root_turn)
    if time_for_move > 0:
        timer = Timer(time_for_move, clear_flag, args=[options.flag])
        timer.start()

    # load model if needed
    if options.heuristic == 'neuralnetwork' and options.network == 'regression':
        if options.model_file == '<default>':
            options.model = load_model('regression.h5')
        else:
            options.model = load_model(options.model_file)
    elif options.heuristic == 'neuralnetwork' and options.network == 'classification':
        if options.model_file == '<default>':
            options.model = load_model('classification.h5')
        else:
            options.model = load_model(options.model_file)
    elif options.heuristic == "random":
        go_params.depth = 1

    # main loop of iterative expansion
    while depth < go_params.depth and options.flag.is_set():
        # search
        temp_eval, temp_nodes_count, temp_pv = negamax(
            root, depth + 1, -100000, 100000, options.flag, options)

        if options.flag.is_set():
            evaluation = temp_eval
            pv = temp_pv
            nodes_count = temp_nodes_count
            depth += 1

            current_time = time.time() - start + 0.001
            print(f"info depth {depth} score cp {evaluation} nodes {nodes_count} " 
                  f"nps {int(nodes_count / current_time)} time {round(1000 * current_time)} "
                  f"pv {' '.join([str(item) for item in pv])}", flush=True)
            if evaluation > 20000 or evaluation < -20000:
                break

    print(f"bestmove {pv[0]}", flush=True)
    options.model = None
    clear_session()


def clear_flag(flag: Event) -> None:
    """
    Clear go flag to indicate stop of calculation. To be used in timer.
    :param flag: indication whether to calculate
    """
    flag.clear()


def negamax(node: Node, depth: int, alpha: int, beta: int, flag: Event, options: Options
            ) -> tuple[int, int, list[str]]:
    """
    Negamax algorithm to find the best moves from starting position.
    :param node: current board position
    :param depth: maximum allowed depth of calculation
    :param alpha: search parameter alpha
    :param beta: search parameter beta
    :param flag: indication whether we can continue calculation
    :param options: search options
    :return: evaluation, nodes searched and best calculated continuation
    """
    # flag check
    if not flag.is_set():
        return 0, 0, []

    # leaf node
    if depth == 0:
        # 3-fold repetition check
        fen = node.position.split(' ')
        prev = ' '.join(fen[:2])
        if prev in node.previous:
            return 0, 1, []

        # heuristic
        if options.quiescence:
            ev, nodes = quiescence(node.position, alpha, beta, flag, options)
            return ev, nodes, []
        else:
            ev = heuristic(node.position, options)
            node.eval = ev
            return ev, 1, []

    # expansion
    if not node.next:
        board = Board(node.position)
        legal = board.legal_moves
        fen = node.position.split(' ')
        prev = Node(' '.join(fen[:2]))

        # solve problem of no legal moves
        if legal.count() == 0:
            # 3-fold repetition check
            if prev in node.previous:
                return 0, 1, []

            # heuristic
            ev = heuristic(node.position, options)

            node.eval = ev
            return ev, 1, []

        for move in legal:
            board.push(move)
            new = Node(board.fen())
            new.move = move.uci()
            board.pop()
            new.previous = node.previous.copy()
            new.previous.append(prev)
            node.next.append(new)

    # search
    best_pv = []
    nodes = 0
    for new in node.next:
        score, count, pv = negamax(new, depth - 1, -beta, -alpha, flag, options)
        score = -score
        nodes += count
        pv.insert(0, new.move)

        if score >= beta:
            return beta, nodes, []
        if score > alpha:
            alpha = score
            best_pv = pv

    return alpha, nodes, best_pv


def quiescence(fen: str, alpha: int, beta: int, flag: Event, options: Options) -> tuple[int, int]:
    """
    Quiescence search checks all possible captures and checks to ensure not returning
    evaluation of position in-between captures or lost after simple check.
    :param fen: board representation in fen format
    :param alpha: search parameter alpha
    :param beta: search parameter beta
    :param flag: indication whether we can continue calculation
    :param options: search options
    :return: evaluation and nodes searched
    """
    # flag check
    if not flag.is_set():
        return 0, 0

    # heuristic
    stand_pat = heuristic(fen, options)
    nodes = 1

    if stand_pat >= beta:
        return beta, nodes

    board = Board(fen)
    if len(board.piece_map()) > 8:
        delta = True
    else:
        delta = False

    if delta:
        # full delta pruning
        if stand_pat < alpha - 1000:
            return alpha, nodes

    if stand_pat > alpha:
        alpha = stand_pat

    # expansion and search
    legal = board.legal_moves
    for move in legal:
        board.push(move)
        new = board.copy()
        board.pop()

        if board.is_capture(move) or new.is_check():
            # delta pruning
            if delta and board.is_capture(move):
                value = value_captured_piece(board.piece_type_at(move.to_square)) + 200
                if stand_pat + value < alpha:
                    continue

            score, count = quiescence(new.fen(), -beta, -alpha, flag, options)
            score = -score
            nodes += count

            if score >= beta:
                return beta, nodes
            if score > alpha:
                alpha = score
    return alpha, nodes


def value_captured_piece(piece: PieceType) -> int:
    """
    Value of a captured piece.
    :param piece: piece type to be captured
    :return: value of the piece
    """
    if piece == PAWN:
        return PAWN_VALUE
    elif piece == KNIGHT:
        return KNIGHT_VALUE
    elif piece == BISHOP:
        return BISHOP_VALUE
    elif piece == ROOK:
        return ROOK_VALUE
    elif piece == QUEEN:
        return QUEEN_VALUE
    return 0
