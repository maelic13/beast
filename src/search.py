import math
import heuristic

# Various search algorithms

# CLASSES
class searchValues:
    def __init__(self):
        self.bestValue = None
        self.bestMove = None
        self.pv = []

# FUNCTIONS
def search(tree, options):
    if options.searchAlgorithm in ['AlphaBeta', 'alphabeta']:
        sV = alphaBeta(tree.root, -math.inf, math.inf, tree.root.board.turn, options.flag)
    elif options.searchAlgorithm in ['MCTS', 'mcts']:
        sV = MCTS(tree.root, tree.root.board.turn)
    
    if sV != None and options.flag.is_set():
        tree.bestEval = sV.bestValue
        tree.bestMove = sV.bestMove
        tree.pv = sV.pv
    else:
        return

def alphaBeta(node, alpha, beta, turn, flag):
    if not flag.is_set():
        return None

    if node.children == []:
        currentValues = searchValues()
        currentValues.bestValue = node.eval
        return currentValues

    if turn:
        currentValues = searchValues()
        currentValues.bestValue = -math.inf
        for each in node.children:
            previousValues = alphaBeta(each, alpha, beta, not turn, flag)
            alpha = max(alpha, previousValues.bestValue)
            if currentValues.bestValue < previousValues.bestValue:
                currentValues.bestValue = previousValues.bestValue
                currentValues.bestMove = each.board.peek()
                currentValues.pv = previousValues.pv
                currentValues.pv.insert(0, currentValues.bestMove.uci())
            if beta <= alpha:
                break
        return currentValues
    else:
        currentValues = searchValues()
        currentValues.bestValue = math.inf
        for each in node.children:
            previousValues = alphaBeta(each, alpha, beta, not turn, flag)
            beta = min(beta, previousValues.bestValue)
            if currentValues.bestValue > previousValues.bestValue:
                currentValues.bestValue = previousValues.bestValue
                currentValues.bestMove = each.board.peek()
                currentValues.pv = previousValues.pv
                currentValues.pv.insert(0, currentValues.bestMove.uci())
            if beta <= alpha:
                break
        return currentValues

def MCTS(tree, turn):
    currentValues = searchValues()
    return currentValues