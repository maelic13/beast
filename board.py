import chess
import sys
import time
from queue import Queue
import math
import io
import sys
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

    def makeMove(self, move):
        self.board.push(chess.Move.from_uci(move))

    def setFen(self, fen):
        self.board = chess.Board(fen)
    
    def clearBoard(self):
        self.board.clear()

class searchTree:
    def __init__(self):
        self.root = node(chess.Board())
        self.depth = 0
        self.seldepth = 0
        self.evaluateNodeQueue = Queue(maxsize=0)
        self.closed = []
        self.nodesCount = 0
        self.timeStart = None
        self.bestMove = None
        self.pv = ''
        self.bestEval = None
        self.run = False
        self.fiftyMoveRule = True

    def setPosition(self, fen, moves):
        board = chess.Board(fen)
        self.root = node(board)
        if not moves == None:
            for each in moves:
                self.root.makeMove(each)
        self.depth = 0        

    def go(self, depth):
        self.timeStart = time.time()
        self.evaluateNodeQueue.put(self.root)
        self.evaluateNodes()
        while (self.depth < depth) or (depth == 0):
            self.expand(self.root)
            self.evaluateNodes()
            sV = self.alphaBeta(self.root, -math.inf, math.inf, self.root.getBoard().turn)
            self.bestEval = sV.bestValue
            self.bestMove = sV.bestMove
            self.pv = sV.pv
            print('info depth', self.depth, 'seldepth', self.seldepth, 'score cp', int(self.bestEval), 'nodes', self.nodesCount, 'nps', self.nodesPerSecond(), 'time', round(1000*self.getTime()), 'pv', ' '.join([str(item) for item in self.pv]), flush=True)
            self.depth += 1
            if self.seldepth < self.depth:
                self.seldepth = self.depth
        print('bestmove', self.bestMove, flush=True)

    def setDepth(self, depth):
        self.depth = depth

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
            if current.getBoard().is_game_over():
                if current.getBoard().is_checkmate() and current.getBoard().turn:
                    current.setEval(-10000)
                    continue
                elif current.getBoard().is_checkmate() and (not current.getBoard().turn):
                    current.setEval(10000)
                    continue
                elif current.getBoard().is_stalemate():
                    current.setEval(0)
                    continue
            elif current.getBoard().is_insufficient_material():
                    current.setEval(0)
                    continue
            elif current.getBoard().can_claim_threefold_repetition():
                    current.setEval(0)
                    continue
            elif current.getBoard().can_claim_fifty_moves() and self.fiftyMoveRule:
                    current.setEval(0)
                    continue
            else:
                evalTable = [100, 295, 315, 500, 900]
                eval = 0
                for i in range(0, 64):
                    piece = current.getBoard().piece_at(i)
                    pieceValue = 0
                    if piece == chess.Piece(chess.PAWN, chess.WHITE):
                        pieceValue = evalTable[0]
                    elif piece == chess.Piece(chess.PAWN, chess.BLACK):
                        pieceValue = -evalTable[0]
                    elif piece == chess.Piece(chess.KNIGHT, chess.WHITE):
                        pieceValue = evalTable[1]
                    elif piece == chess.Piece(chess.KNIGHT, chess.BLACK):
                        pieceValue = -evalTable[1]
                    elif piece == chess.Piece(chess.BISHOP, chess.WHITE):
                        pieceValue = evalTable[2]
                    elif piece == chess.Piece(chess.BISHOP, chess.BLACK):
                        pieceValue = -evalTable[2]
                    elif piece == chess.Piece(chess.ROOK, chess.WHITE):
                        pieceValue = evalTable[3]
                    elif piece == chess.Piece(chess.ROOK, chess.BLACK):
                        pieceValue = -evalTable[3]
                    elif piece == chess.Piece(chess.QUEEN, chess.WHITE):
                        pieceValue = evalTable[4]
                    elif piece == chess.Piece(chess.QUEEN, chess.BLACK):
                        pieceValue = -evalTable[4]
                    
                    #add square and other conditions
                    if i==27 or i==28 or i==35 or i==36:
                        pieceValue = pieceValue * 1.05
                    '''
                    if current.getBoard().turn:
                        opponentKing = current.getBoard().king(chess.BLACK)
                        distance = math.sqrt((opponentKing%8 - i%8)^2 + (int(opponentKing/8) - int(i/8))^2)
                        pieceValue += 0.3 - distance*0.01
                    else:
                        opponentKing = current.getBoard().king(chess.WHITE)
                    '''
                    eval += pieceValue
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

    '''
    def countMemoryUsage(self): # NOT WORKING!
        count = sys.getsizeof(self)
        for x in self.nodes:
            for y in x:
                count += sys.getsizeof(y)
        return count
    '''

    def nodesPerSecond(self):
        try:
            nps = round(self.getNodes() / self.getTime())
        except:
            nps = self.getNodes()
        return nps

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

    def setFiftyMoveRule(self, value):
        self.fiftyMoveRule = value

class searchValues:
    def __init__(self):
        self.bestValue = None
        self.bestMove = None
        self.pv = []