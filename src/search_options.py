from constants import Constants


class SearchOptions:
    """
    Search options for engine.

    fen: string representing board position
    played moves: additional moves made from board position in fen
    white_time: white's remaining time in milliseconds
    white_increment: increment for every move white makes
    black_time: black's time in milliseconds
    black_increment: increment for every move black makes
    depth: maximal allowed depth of calculation
    """
    def __init__(self) -> None:
        self.fen: str = Constants.START_POSITION
        self.played_moves: list[str] = []

        self.white_time: int = 0
        self.white_increment: int = 0
        self.black_time: int = 0
        self.black_increment: int = 0
        self.depth: int = 0

    def __str__(self) -> str:
        return (f"SearchOptions(\n"
                f"\tfen: {self.fen}\n"
                f"\tplayed moves: {self.played_moves}\n"
                f"\twhite time: {self.white_time}\n"
                f"\twhite increment: {self.white_increment}\n"
                f"\tblack time: {self.black_time}\n"
                f"\tblack increment: {self.black_increment}\n"
                f"\tdepth: {self.depth}\n"
                f")\n")

    def reset(self):
        """ Reset all options. """
        self.reset_position()
        self.reset_search_parameters()

    def set_position(self, args: list[str]) -> None:
        """ Parse arguments and set position. """
        self.reset_position()

        if args[0] == "fen":
            self.fen = " ".join(args[1:args.index("moves")])
        if "moves" in args:
            self.played_moves = args[args.index("moves") + 1:]

    def set_search_parameters(self, _args: list[str]) -> None:
        """ Parse arguments and set search parameters. """
        self.reset_search_parameters()

    def reset_position(self) -> None:
        """ Reset position only, including played moves. """
        self.fen = Constants.START_POSITION
        self.played_moves = []

    def reset_search_parameters(self) -> None:
        """ Reset search parameters only. """
        self.white_time = 0
        self.white_increment = 0
        self.black_time = 0
        self.black_increment = 0
        self.depth = 0
