import logging
logging.getLogger('tensorflow').setLevel(logging.FATAL)

import time

from chess import Board
from tensorflow.keras.models import load_model
from tensorflow.keras.backend import clear_session
from threading import Timer

import heuristic
import timemanagement as tm


class Node:
    def __init__(self, fen):
        self.position = fen
        self.move = None
        self.eval = None
        self.next = []
        self.previous = []


def main(goParams, options):
    # initialize values
    root = goParams.root
    depth = 0
    if root.position.split(' ')[1] == 'w':
        root_turn = True
    else:
        root_turn = False

    # time management + timer
    start = time.time()
    timeForMove = tm.timeForMove(goParams, options, root_turn)
    if timeForMove > 0:
        timer = Timer(timeForMove, clearFlag, args=[options.flag])
        timer.start()

    # load model if needed
    if options.heuristic == 'NeuralNetwork' and options.network == 'Regression':
        if options.modelFile == '<default>':
            options.model = load_model('regression.h5')
        else:
            options.model = load_model(options.modelFile)
    elif options.heuristic == 'NeuralNetwork' and options.network == 'Classification':
        if options.modelFile == '<default>':
            options.model = load_model('classification.h5')
        else:
            options.model = load_model(options.modelFile)

    # main loop of iterative expansion
    while conditionsMet(depth, goParams, options.flag):
        # search
        temp_eval, temp_nodes_count, temp_pv = negamax(
            root, depth + 1, -100000, 100000, options.flag, options)

        if options.flag.is_set():
            eval = temp_eval
            pv = temp_pv
            nodes_count = temp_nodes_count
            depth += 1

            current_time = time.time() - start + 0.001
            print(
                'info depth', depth,  # 'seldepth', len(pv),
                'score cp', int(eval), 'nodes', nodes_count,
                'nps', int(nodes_count / current_time), 'time', round(1000 * current_time),
                'pv', ' '.join([str(item) for item in pv]),
                flush=True)
            if eval > 20000 or eval < -20000:
                break

    print('bestmove', pv[0], flush=True)
    options.model = None
    clear_session()


def clearFlag(flag):
    flag.clear()


def conditionsMet(depth, goParams, flag):
    if depth == goParams.depth or not flag.is_set():
        return False
    else:
        return True


def negamax(node, depth, alpha, beta, flag, options):
    # flag check
    if not flag.is_set():
        return 0, 0, []

    # leaf node
    if(depth == 0):
        # 3-fold repetition check
        fen = node.position.split(' ')
        prev = ' '.join(fen[:2])
        if prev in node.previous:
            return 0, 1, []

        # heuristic
        if options.quiescence:
            ev, nodes = quiesce(node.position, alpha, beta, flag, options)
            return ev, nodes, []
        else:
            if options.heuristic == 'NeuralNetwork':
                ev = heuristic.nn_heuristic(node.position, options, options.model)
            elif options.heuristic == 'Random':
                ev = heuristic.random_heuristic()
            else:
                ev = heuristic.heuristic(node.position, options)

            node.eval = ev
            return ev, 1, []

    # expansion
    if node.next == []:
        board = Board(node.position)
        legal = board.legal_moves
        fen = node.position.split(' ')
        prev = ' '.join(fen[:2])

        # solve problem of no legal moves
        if legal.count() == 0:
            # 3-fold repetition check
            if prev in node.previous:
                return 0, 1, []

            # heuristic
            if options.heuristic == 'NeuralNetwork':
                ev = heuristic.nn_heuristic(node.position, options, options.model)
            elif options.heuristic == 'Random':
                ev = heuristic.random_heuristic()
            else:
                ev = heuristic.heuristic(node.position, options)

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

        if(score >= beta):
            return beta, nodes, []
        if(score > alpha):
            alpha = score
            best_pv = pv

    return alpha, nodes, best_pv


def quiesce(fen, alpha, beta, flag, options):
    # flag check
    if not flag.is_set():
        return 0, 0

    # heuristic
    if options.heuristic == 'NeuralNetwork':
        stand_pat = heuristic.nn_heuristic(fen, options, options.model)
    elif options.heuristic == 'Random':
        stand_pat = heuristic.random_heuristic()
    else:
        stand_pat = heuristic.heuristic(fen, options)

    nodes = 1

    if(stand_pat >= beta):
        return beta, nodes

    board = Board(fen)
    if len(board.piece_map()) > 8:
        delta = True
    else:
        delta = False

    if delta:
        # full delta pruning
        if (stand_pat < alpha - 1000):
            return alpha, nodes

    if(stand_pat > alpha):
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
                if (stand_pat + value < alpha):
                    continue

            score, count = quiesce(new.fen(), -beta, -alpha, flag, options)
            score = -score
            nodes += count

            if(score >= beta):
                return beta, nodes
            if(score > alpha):
                alpha = score
    return alpha, nodes


def value_captured_piece(piece):
    if piece == 1:
        return 100
    elif piece == 2 or piece == 3:
        return 350
    elif piece == 4:
        return 525
    elif piece == 5:
        return 1000
    else:
        return 0
