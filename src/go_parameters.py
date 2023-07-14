from node import Node


class GoParameters:
    """ Structure to store engine search parameters. """
    def __init__(self) -> None:
        """ Constructor. """
        # position
        self.moves = ""
        self.root = Node("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

        # time parameters
        self.wtime: int | None = None
        self.btime: int | None = None
        self.winc: int | None = None
        self.binc: int | None = None
        self.movesToGo: int | None = None
        self.movetime: int | None = None

        # depth parameters
        self.depth: int = 128
        self.nodes: int | None = None
        self.mate: int | None = None

        # continuous parameters
        self.infinite = False
        self.ponder = False

    def reset(self):
        """ Reset the parameters to default values. """
        self.moves = ""
        self.wtime = None
        self.btime = None
        self.winc = None
        self.binc = None
        self.ponder = False
        self.movesToGo = None
        self.depth = 128
        self.nodes = None
        self.mate = None
        self.movetime = None
        self.infinite = False
