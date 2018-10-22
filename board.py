import chess
import sys
import time
from queue import Queue
import math

# VARIABLES

# CLASSES
class node:
    def __init__(self, board):
        self.board = board
        self.eval = None
        self.parent = None
        self.children = []

    def getBoard(self):
        return self.board

    def addChild(self, child):
        self.children.append(child)

    def setParent(self, parent):
        self.parent = parent

    def getParent(self):
        return self.parent

    def getChildren(self):
        return self.children

    def setEval(self,eval):
        self.eval = eval

    def getEval(self):
        return self.eval

class searchTree:
    def __init__(self):
        self.root = None
        self.depth = 0
        self.evaluateNodeQueue = Queue(maxsize=0)
        self.closed = []
        self.nodesCount = 0
        self.timeStart = None
        self.bestMove = None
        self.pv = ''
        self.bestEval = None
        self.run = False

    def setPosition(self, fen):
        board = chess.Board(fen)
        self.root = node(board)

    def go(self, depth):
        self.timeStart = time.time()
        self.evaluateNodeQueue.put(self.root)
        self.evaluateNodes()
        while (self.depth < depth) or (depth == 0):
            self.expand(self.root)
            self.depth += 1
            self.evaluateNodes()
            sV = self.alphaBeta(self.root, -math.inf, math.inf, self.root.getBoard().turn)
            self.bestEval = sV.bestValue
            self.bestMove = sV.bestMove
            self.pv = sV.pv
            print('info depth', self.depth, 'score cp', self.bestEval, 'nodes', self.nodesCount, 'nps', self.nodesPerSecond(), 'time', round(1000*self.getTime()), 'pv', ' '.join([str(item) for item in self.pv]))
        print('bestmove', self.bestMove)

    def expand(self, current):
        if current.children == []:
            legalMoves = current.getBoard().legal_moves
            for each in legalMoves:
                current.board.push(each)
                new = node(current.board.copy())
                current.board.pop()
                current.addChild(new)
                new.setParent(current)
                self.evaluateNodeQueue.put(new)
                self.nodesCount += 1
        else:   
            for each in current.children:
                self.expand(each)
                self.nodesCount += 1

    def evaluateNodes(self):
        while not self.evaluateNodeQueue.empty():
            current = self.evaluateNodeQueue.get()
            fen = current.getBoard().fen()
            whiteRooks, blackRooks, whiteBishops, blackBishops, whiteKnights, blackKnights, whitePawns, blackPawns, whiteQueens, blackQueens = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            if current.getBoard().is_game_over():
                if current.getBoard().is_checkmate() and current.getBoard().turn:
                    current.setEval(-256)
                elif current.getBoard().is_checkmate() and (not current.getBoard().turn):
                    current.setEval(256)
                elif current.getBoard().is_stalemate():
                    current.setEval(0)
            elif current.getBoard().is_insufficient_material():
                    current.setEval(0)
            elif current.getBoard().can_claim_threefold_repetition():
                    current.setEval(0)
            elif current.getBoard().can_claim_draw():
                    current.setEval(0)
            else:            
                for each in fen:
                    if each == 'p':
                        whitePawns += 1
                    elif each == 'P':
                        blackPawns += 1
                    elif each == 'n':
                        whiteKnights += 1
                    elif each == 'N':
                        blackKnights += 1
                    elif each == 'b':
                        whiteBishops += 1
                    elif each == 'B':
                        blackBishops += 1
                    elif each == 'r':
                        whiteRooks += 1
                    elif each == 'R':
                        blackRooks += 1
                    elif each == 'q':
                        whiteQueens += 1
                    elif each == 'Q':
                        blackQueens += 1
                
                evalTable = [100, 295, 315, 500, 900]
                eval = evalTable[0]*whitePawns + evalTable[1]*whiteKnights + evalTable[2]*whiteBishops + evalTable[3]*whiteRooks + evalTable[4]*whiteQueens - evalTable[0]*blackPawns - evalTable[1]*blackKnights - evalTable[2]*blackBishops - evalTable[3]*blackRooks - evalTable[4]*blackQueens
                eval = round(eval)
                current.setEval(eval)
            self.nodesCount += 1
        
    def alphaBeta(self, node, alpha, beta, turn):
        if node.getChildren() == []:
            currentValues = searchValues()
            currentValues.bestValue = node.getEval()
            return currentValues

        if turn:
            currentValues = searchValues()
            currentValues.bestValue = -math.inf
            for each in node.getChildren():
                previousValues = self.alphaBeta(each, alpha, beta, not turn)
                alpha = max(alpha, previousValues.bestValue)
                if currentValues.bestValue < previousValues.bestValue:
                    currentValues.bestValue = previousValues.bestValue
                    currentValues.bestMove = each.getBoard().peek()
                    currentValues.pv = previousValues.pv
                    currentValues.pv.insert(0, currentValues.bestMove.uci())
                if beta <= alpha:
                    break
            return currentValues
        else:
            currentValues = searchValues()
            currentValues.bestValue = math.inf
            for each in node.getChildren():
                previousValues = self.alphaBeta(each, alpha, beta, not turn)
                beta = min(beta, previousValues.bestValue)
                if currentValues.bestValue > previousValues.bestValue:
                    currentValues.bestValue = previousValues.bestValue
                    currentValues.bestMove = each.getBoard().peek()
                    currentValues.pv = previousValues.pv
                    currentValues.pv.insert(0, currentValues.bestMove.uci())
                if beta <= alpha:
                    break
            return currentValues

    def getNodes(self):
        return self.nodesCount

    def getRoot(self):
        return self.root

    def countMemoryUsage(self): # NOT WORKING!
        count = sys.getsizeof(self)
        for x in self.nodes:
            for y in x:
                count += sys.getsizeof(y)
        return count

    def nodesPerSecond(self):
        return round(self.getNodes() / self.getTime())

    def getTime(self):
        tm = time.time() - self.timeStart
        return tm

    def printTreeFens(self, node):
        if not node.getChildren() == []:
            for each in node.getChildren():
                self.printTreeFens(each)
            print(node.getBoard().fen())
        else:
            print(node.getBoard().fen())


class searchValues:
    def __init__(self):
        self.bestValue = None
        self.bestMove = None
        self.pv = []

# MAIN
'''
board = chess.Board('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
tree = searchTree(board)
tree.go(2)
print(tree.bestEval)
print(tree.bestMove)
print (' '.join([str(item) for item in tree.pv]))
#tree.printTreeFens(tree.root)
'''