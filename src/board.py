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
        self.depth = 0
        self.children = []
        self.tablebasePosition = False

    def addChild(self, child):
        self.children.append(child)

    def setParent(self, parent):
        self.parent = parent

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

    def setPosition(self, fen, moves):
        board = chess.Board(fen)
        self.root = node(board)
        if not moves == None:
            for each in moves:
                self.root.board.push(chess.Move.from_uci(each))
        self.depth = 0
        self.seldepth = 0
        self.nodesCount = 0

    def go(self, goParams, options):
        # time management + timer
        self.timeStart = time.time()
        timeForMove = tm.timeForMove(goParams, options, self.root.board.turn)
        if timeForMove > 0: 
            timer = Timer(timeForMove, self.clearFlag, args=[options.flag])
            timer.start()
        heuristic.heuristic(self.root, options)

        # main loop of iterative expansion
        while self.conditionsMet(goParams, options.flag):
            # expansion
            expand.expand(self, goParams, options)

            # search
            search.search(self, options)

            if options.flag.is_set():
                self.depth += 1

            print(
                'info depth', self.depth, #'seldepth', self.seldepth,
                'score cp', int(self.bestEval), 'nodes', self.nodesCount,
                'nps', self.nodesPerSecond(), 'time', round(1000*self.getTime()),
                'pv', ' '.join([str(item) for item in self.pv]),
                flush=True
                )
        
        print('bestmove', self.bestMove, flush=True)

    def nodesPerSecond(self):
        try:
            nps = round(self.nodesCount / self.getTime())
        except:
            nps = self.nodesCount
        return nps

    def getTime(self):
        return time.time() - self.timeStart

    def clearFlag(self, flag):
        flag.clear()
        with self.expandQueue.mutex:
            self.expandQueue.queue.clear()

    def conditionsMet(self, goParams, flag):
        if self.depth == goParams.depth or not flag.is_set():
            return False
        else:
            return True