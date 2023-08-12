from pathlib import Path

from chess import Board

from constants import Constants
from heuristic import HeuristicType


class SearchOptions:
    """
    Search options for engine.

    board: chess board representation
    heuristic_type: what heuristic to use for evaluation
        - classical
        - legacy_neural_network
        - neural_network

    movetime: time for current move in milliseconds
    white_time: white's remaining time in milliseconds
    white_increment: increment for every move white makes
    black_time: black's time in milliseconds
    black_increment: increment for every move black makes
    depth: maximal allowed depth of calculation
    """
    def __init__(self) -> None:
        self.board = Board()

        self.movetime: int = 0  # [ms]
        self.white_time: int = 0  # [ms]
        self.white_increment: int = 0  # [ms]
        self.black_time: int = 0  # [ms]
        self.black_increment: int = 0  # [ms]
        self.depth: float = Constants.INFINITE_DEPTH

        self.fifty_moves_rule = True
        self.heuristic_type = HeuristicType.CLASSICAL
        self.syzygy_path: Path | None = None
        self.syzygy_probe_limit: int = 7

    def __str__(self) -> str:
        return (f"SearchOptions(\n"
                f"\tboard: {self.board}\n"
                f"\tmove time: {self.movetime}\n"
                f"\twhite time: {self.white_time}\n"
                f"\twhite increment: {self.white_increment}\n"
                f"\tblack time: {self.black_time}\n"
                f"\tblack increment: {self.black_increment}\n"
                f"\tdepth: {self.depth}\n"
                f"\tfifty moves rule: {self.fifty_moves_rule}\n"
                f"\theuristic type: {self.heuristic_type}\n"
                f"\tsyzygy path: {self.syzygy_path}\n"
                f"\tsyzygy probe limit: {self.syzygy_probe_limit}\n"
                f")\n")

    @staticmethod
    def get_uci_options() -> list[str]:
        """
        Available options to be set in uci string format.
        :return: list of uci formatted options
        """
        return [
            "option name Heuristic type combo default classical var classical var random",
            "option name Syzygy50MoveRule type check default true",
            "option name SyzygyPath type string default <empty>",
            "option name SyzygyProbeLimit type spin default 7 min 0 max 7",
        ]

    def reset(self):
        """ Reset search options and board. """
        self.board = Board()
        self.reset_temporary_parameters()

    def set_position(self, args: list[str]) -> None:
        """ Parse arguments and set position. """
        self.board = Board()

        if args[0] == "fen" and "moves" not in args:
            self.board = Board(" ".join(args[1:]))
            return
        elif "moves" not in args:
            return

        if args[0] == "fen":
            self.board = Board(" ".join(args[1:args.index("moves")]))

        for move in args[args.index("moves") + 1:]:
            self.board.push_uci(move)

    def set_search_parameters(self, args: list[str]) -> None:
        """ Parse arguments and set search parameters. """
        self.reset_temporary_parameters()

        # special case where 'go' is called with no arguments
        if not args:
            self.depth = Constants.DEFAULT_DEPTH
            return

        # parse possible 'go' arguments
        if "movetime" in args:
            self.movetime = int(args[args.index("movetime") + 1])
        if "wtime" in args:
            self.white_time = int(args[args.index("wtime") + 1])
        if "winc" in args:
            self.white_increment = int(args[args.index("winc") + 1])
        if "btime" in args:
            self.black_time = int(args[args.index("btime") + 1])
        if "binc" in args:
            self.black_increment = int(args[args.index("binc") + 1])
        if "depth" in args:
            self.depth = int(args[args.index("depth") + 1])
        if "infinite" in args:
            self.depth = Constants.INFINITE_DEPTH

    def set_option(self, args: list[str]) -> None:
        """
        Set search option, not changed until specific action (no reset).
        :param args: arguments of setoption command
        """
        option_name = args[1].lower()
        value = " ".join(args[3:]).lower()

        match option_name:
            case "heuristic":
                try:
                    self.heuristic_type = HeuristicType.from_str(value)
                except RuntimeError as err:
                    print(err)
            case "syzygypath":
                path = Path(value.replace('\\', '/'))
                self.syzygy_path = path if path.exists() else None
            case "syzygyprobelimit":
                self.syzygy_probe_limit = int(value)
            case "syzygy50moverule":
                self.fifty_moves_rule = value == "true"

    @property
    def time_options(self) -> dict[str, int]:
        """
        Return dictionary with time options as values and their UCI names as keys.
        :return: time options with their UCI names.
        """
        return {
            "movetime": self.movetime,
            "wtime": self.white_time,
            "winc": self.white_increment,
            "btime": self.black_time,
            "binc": self.black_increment
        }

    @property
    def has_time_options(self) -> bool:
        """ Information whether any time option is present. """
        return any(option != 0 for option in self.time_options.values())

    def reset_temporary_parameters(self) -> None:
        """ Reset temporary parameters only. """
        self.movetime = 0
        self.white_time = 0
        self.white_increment = 0
        self.black_time = 0
        self.black_increment = 0
        self.depth = Constants.INFINITE_DEPTH
