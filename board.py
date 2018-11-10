import chess
import time
from queue import Queue
from threading import Timer
import math
import search
import expand
import timemanagement as tm
import heuristic

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
        self.expandQueue = Queue(maxsize=0)
        self.nodesCount = 0
        self.timeStart = None
        self.bestMove = None
        self.pv = ''
        self.bestEval = None
        self.fiftyMoveRule = True

    def setPosition(self, fen, moves):
        board = chess.Board(fen)
        self.root = node(board)
        if not moves == None:
            for each in moves:
                self.root.makeMove(each)
        self.depth = 0
        self.seldepth = 0

    def go(self, goParams, options, flag):
        # time management + timer
        self.timeStart = time.time()
        timeForMove = tm.timeForMove(goParams, options, self.root.getBoard().turn)
        if timeForMove > 0: 
            timer = Timer(timeForMove, self.clearFlag, args=[flag])
            timer.start()

        # main loop of iterative expansion
        while flag.is_set() and self.conditionsMet(goParams):
            # expansion
            expand.expand(self, goParams, options, flag)

            # search
            search.search(self, options)
            self.depth += 1

            print(
                'info depth', self.depth, 'seldepth', self.seldepth,
                'score cp', int(self.bestEval), 'nodes', self.nodesCount,
                'nps', self.nodesPerSecond(), 'time', round(1000*self.getTime()),
                'pv', ' '.join([str(item) for item in self.pv]),
                flush=True
                )
        
        try:
            print('bestmove', self.bestMove, 'ponder', self.pv[1], flush=True)
        except:
            print('bestmove', self.bestMove, flush=True)

    def getNodes(self):
        return self.nodesCount

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

    def clearFlag(self, flag):
        flag.clear()
        with self.expandQueue.mutex:
            self.expandQueue.queue.clear()
    def conditionsMet(self, goParams):
        if self.depth == goParams.depth:
            return False
        else:
            return True