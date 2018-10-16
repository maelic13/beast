import chess
from queue import Queue

class node:
    def __init__(self, fen):
        self.board = chess.Board(fen)
        self.eval = None
        self.parent = None
        self.children = []

    def getBoard(self):
        return self.board

    def addChild(self, child):
        self.children.append(node(child))

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
    def __init__(self, root):
        self.root = node(root)
        self.depth = 0
        self.opened = Queue(maxsize=0)
        self.closed = []
        self.nodes = 0

    def search(self, depth):
        while (self.depth < depth) | (depth == 0):
            self.expand(self.root)
            self.depth += 1

    def expand(self, current):
        if current.children == []:
            legalMoves = current.getBoard().legal_moves
            for each in legalMoves:
                current.addChild(current.getBoard().fen(each))
            for each in current.children:
                each.setEval(self.heuristic(each.getBoard()))
                self.nodes += 1
        else:
            for each in current.children:
                self.expand(each)

    def heuristic(self,position):
        return 0

    def getNodes(self):
        return self.nodes


# MAIN
tree = searchTree("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
tree.search(2)
print(tree.getNodes())