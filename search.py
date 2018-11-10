import math

# Various search algorithms

# CLASSES
class searchValues:
    def __init__(self):
        self.depth = 0
        self.bestValue = None
        self.bestMove = None
        self.pv = []

# FUNCTIONS
def search(tree, options):
    if options.searchAlgorithm in ['AlphaBeta', 'alphabeta']:
        sV = alphaBeta(tree.root, -math.inf, math.inf, tree.root.getBoard().turn)
    elif options.searchAlgorithm in ['MCTS', 'mcts']:
        sV = MCTS(tree.root, tree.root.getBoard().turn)
    tree.bestEval = sV.bestValue
    tree.bestMove = sV.bestMove
    tree.pv = sV.pv
    tree.seldepth = sV.depth

def alphaBeta(node, alpha, beta, turn):
    if node.getChildren() == []:
        currentValues = searchValues()
        currentValues.bestValue = node.getEval()
        return currentValues

    if turn:
        currentValues = searchValues()
        currentValues.bestValue = -math.inf
        for each in node.getChildren():
            previousValues = alphaBeta(each, alpha, beta, not turn)
            alpha = max(alpha, previousValues.bestValue)
            if currentValues.bestValue < previousValues.bestValue:
                currentValues.bestValue = previousValues.bestValue
                currentValues.bestMove = each.getBoard().peek()
                currentValues.pv = previousValues.pv
                currentValues.pv.insert(0, currentValues.bestMove.uci())
            if beta <= alpha:
                break
        currentValues.depth += 1
        return currentValues
    else:
        currentValues = searchValues()
        currentValues.bestValue = math.inf
        for each in node.getChildren():
            previousValues = alphaBeta(each, alpha, beta, not turn)
            beta = min(beta, previousValues.bestValue)
            if currentValues.bestValue > previousValues.bestValue:
                currentValues.bestValue = previousValues.bestValue
                currentValues.bestMove = each.getBoard().peek()
                currentValues.pv = previousValues.pv
                currentValues.pv.insert(0, currentValues.bestMove.uci())
            if beta <= alpha:
                break
        currentValues.depth += 1
        return currentValues

def MCTS(tree, turn):
    currentValues = searchValues()
    return currentValues