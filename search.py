import chess
import board
from queue import Queue

class searchTree:
    def __init__(self, init):
        self.root = init

    def wideSearch(self, position, depth):
        opened = Queue(maxsize=0)
        closed = []

        for each in position.position.legal_moves:
            opened.put(each)


# MAIN
