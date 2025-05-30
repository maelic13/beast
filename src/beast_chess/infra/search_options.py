from multiprocessing import cpu_count
from pathlib import Path

from chess import Board

from beast_chess.heuristics import HeuristicType

from .constants import Constants


class SearchOptions:
    """
    Search options for engine.

    board: chess board representation
    heuristic_type: what heuristic to use for evaluation, see HeuristicType

    move_time: time for current move in milliseconds
    white_time: white's remaining time in milliseconds
    white_increment: increment for every move white makes
    black_time: black's time in milliseconds
    black_increment: increment for every move black makes
    depth: maximal allowed depth of calculation
    """

    def __init__(self) -> None:
        self.board = Board()

        self.move_time: int = 0  # [ms]
        self.white_time: int = 0  # [ms]
        self.white_increment: int = 0  # [ms]
        self.black_time: int = 0  # [ms]
        self.black_increment: int = 0  # [ms]
        self.depth: int = Constants.INFINITE_DEPTH

        self.fifty_moves_rule = True
        self.heuristic_type = HeuristicType.CLASSICAL
        self.model_file: Path | None = None
        self.syzygy_path: Path | None = None
        self.syzygy_probe_limit: int = 7
        self.threads: int = 1

    def __str__(self) -> str:
        return (
            f"SearchOptions(\n"
            f"\tboard: {self.board}\n"
            f"\tmove time: {self.move_time}\n"
            f"\twhite time: {self.white_time}\n"
            f"\twhite increment: {self.white_increment}\n"
            f"\tblack time: {self.black_time}\n"
            f"\tblack increment: {self.black_increment}\n"
            f"\tdepth: {self.depth}\n"
            f"\tfifty moves rule: {self.fifty_moves_rule}\n"
            f"\theuristic type: {self.heuristic_type}\n"
            f"\tmodel file: {self.model_file}\n"
            f"\tsyzygy path: {self.syzygy_path}\n"
            f"\tsyzygy probe limit: {self.syzygy_probe_limit}\n"
            f"\tthreads: {self.threads}\n"
            f")\n"
        )

    @staticmethod
    def get_uci_options() -> list[str]:
        """
        Available options to be set in uci string format.
        :return: list of uci formatted options
        """
        options = SearchOptions()
        return [
            f"option name Heuristic type combo "
            f"default {options.heuristic_type.name.lower()} "
            f"var {' var '.join(h.name.lower() for h in HeuristicType)}",
            f"option name ModelFile type string default {options.model_file or '<empty>'!s} ",
            f"option name Syzygy50MoveRule type check default "
            f"{str(options.fifty_moves_rule).lower()}",
            f"option name SyzygyPath type string "
            f"default {str(options.syzygy_path) if options.syzygy_path else '<empty>'}",
            f"option name SyzygyProbeLimit type spin default {options.syzygy_probe_limit} "
            f"min 0 max 7",
            f"option name Threads type spin default {options.threads} min 1 max {cpu_count()}",
        ]

    def reset(self) -> None:
        """Reset search options and board."""
        self.board = Board()
        self.reset_temporary_parameters()

    def set_position(self, args: list[str]) -> None:
        """Parse arguments and set position."""
        self.board = Board()

        if args[0] == "fen" and "moves" not in args:
            self.board = Board(" ".join(args[1:]))
            return
        if "moves" not in args:
            return

        if args[0] == "fen":
            self.board = Board(" ".join(args[1 : args.index("moves")]))

        for move in args[args.index("moves") + 1 :]:
            self.board.push_uci(move)

    def set_search_parameters(self, args: list[str]) -> None:
        """Parse arguments and set search parameters."""
        self.reset_temporary_parameters()

        # special case where 'go' is called with no arguments
        if not args:
            self.depth = Constants.DEFAULT_DEPTH
            return

        # parse possible 'go' arguments
        if "movetime" in args:
            self.move_time = int(args[args.index("movetime") + 1])
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

    def set_option(self, args: list[str]) -> None:  # noqa: C901, PLR0912
        """
        Set the search option, not changed until a specific action (no reset).
        :param args: arguments of setoption command
        """
        option_name = args[1].lower()
        value = " ".join(args[3:])

        match option_name:
            case "syzygy50moverule":
                match value.lower():
                    case "true":
                        self.fifty_moves_rule = True
                    case "false":
                        self.fifty_moves_rule = False
                    case _:
                        print("Invalid syzygy 50 move rule.")
            case "heuristic":
                try:
                    self.heuristic_type = HeuristicType.from_str(value)
                except RuntimeError as err:
                    print(err)
            case "modelfile":
                path = Path(value.replace("\\", "/"))
                if not path.exists():
                    print("Invalid model file.")
                    return
                self.model_file = path
            case "syzygypath":
                path = Path(value.replace("\\", "/"))
                if not path.exists():
                    print("Invalid syzygy path.")
                    return
                self.syzygy_path = path
            case "syzygyprobelimit":
                try:
                    self.syzygy_probe_limit = int(value)
                except ValueError:
                    print("Invalid syzygy probe limit.")
            case "threads":
                try:
                    self.threads = int(value)
                except ValueError:
                    print("Invalid thread limit.")

    def reset_temporary_parameters(self) -> None:
        """Reset temporary parameters only."""
        self.move_time = 0
        self.white_time = 0
        self.white_increment = 0
        self.black_time = 0
        self.black_increment = 0
        self.depth = Constants.INFINITE_DEPTH
