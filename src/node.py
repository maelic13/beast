class Node:
    """
    Structure to store board state for search.
    """
    def __init__(self, fen: str) -> None:
        """
        Constructor.
        :param fen: board position representation in FEN string format
        """
        self.position = fen
        self.move: str | None = None
        self.eval: int | None = None
        self.next: list[Node] = []
        self.previous: list[Node] = []
