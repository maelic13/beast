from os import environ
from queue import Queue
from threading import Thread

from chess import Board, Move
from cmd import Cmd

from go_parameters import GoParameters
from node import Node
from options import Options
from search import main as search_main


engineName = "Beast 1.5"
author = "Miloslav Macurek"


class UciLoop(Cmd):
    def do_uci(self, arg: str) -> None:
        if options.debug:
            self._log_to_file(f"uci {arg}")

        print(f"id name {engineName}")
        print(f"id author {author}")
        print()
        print(f"option name Threads type spin default {options.threads} min 1 max 1")
        # time flexibility in ms so engine could make a move in time and did not lose on time
        print(f"option name TimeFlex type spin default {options.time_flex} min 0 max 1000")
        # types of search algorithms
        print(f"option name SearchAlgorithm type combo default {options.search_algorithm} "
              f"var AlphaBeta")
        print(f"option name Quiescence type check default {options.quiescence}")
        # path to syzygy tablebases
        print(f"option name SyzygyPath type string default {options.syzygy_path}")
        # probe limit for syzygy
        print(f"option name SyzygyProbeLimit type spin default {options.syzygy_probe_limit} "
              f"min 0 max 7")
        print(f"option name Syzygy50MoveRule type check default {options.fifty_move_rule}")
        print(f"option name Heuristic type combo default {options.heuristic} "
              f"var Classic var NeuralNetwork var Random")
        print(f"option name Network type combo default {options.network} "
              f"var Regression var Classification")
        print(f"option name ModelFile type string default {options.model_file}")
        print("uciok")

    def do_quit(self, arg: str) -> bool:
        """
        Return True to main cmd loop to indicate quit.
        :param arg: possible arguments, not expected with quit command
        :return: true as indication to quit
        """
        if options.debug:
            self._log_to_file(f"quit {arg}")
        return True

    def do_setoption(self, arg: str) -> None:
        if options.debug:
            self._log_to_file(f"setoption {arg}")

        command = arg.split()
        options.set(command[1], command[3])

        if options.debug:
            message = f"{command[1]} = {options.value(command[1])}"
            print(message)
            self._log_to_file(message)

    def do_debug(self, arg: str) -> None:
        options.set("debug", arg)

    def do_isready(self, arg: str) -> None:
        if options.debug:
            self._log_to_file(f"isready {arg}")
        print("readyok")

    def do_go(self, arg: str) -> None:
        if options.debug:
            self._log_to_file(f"go {arg}")

        if arg.startswith("ponder"):
            print("Ponder is currently not supported.")
            return

        task.put(arg)
        options.flag.set()

    def do_stop(self, arg: str) -> None:
        if options.debug:
            self._log_to_file(f"stop {arg}")
        options.flag.clear()

    def do_ucinewgame(self, arg: str) -> None:
        if options.debug:
            self._log_to_file(f"ucinewgame {arg}")
        go_params.position = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def do_position(self, arg: str) -> None:
        if options.debug:
            self._log_to_file(f"position {arg}")

        try:
            command, arguments = arg.split(' ', 1)
        except ValueError:
            command = arg
            arguments = None

        if command == "startpos" and arguments:
            arguments = arguments.split()
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            moves = arguments[1:]
        elif command and not arguments:
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            moves = None
        else:
            try:
                fen, moves = arguments.split(" moves ")
                moves = moves.split()
            except ValueError:
                fen = arguments
                moves = None

        go_params.root = get_root(fen, moves)
        if options.debug:
            print(go_params.root.position)
            self._log_to_file(go_params.root.position)

    @staticmethod
    def _log_to_file(message: str) -> None:
        with open("log.txt", "a") as file:
            file.write(f"{message}\n")


def get_root(fen: str, moves: list[str] | None) -> Node:
    board = Board(fen)
    root = Node(fen)
    if moves is not None:
        for move in moves:
            fen = board.fen().split(' ')
            root.previous.append(Node(" ".join(fen[:2])))
            board.push(Move.from_uci(move))
    root.position = board.fen()
    return root


def parse_params(go_parameters: GoParameters, string: str) -> None:
    run = True
    while run:
        if string == "infinite":
            go_parameters.infinite = True
            break
        elif string == "ponder":
            go_parameters.ponder = True
            break
        elif not string:
            go_parameters.depth = 2
            break
        try:
            command, param, string = string.split(' ', 2)
        except ValueError:
            command, param = string.split(' ', 1)
            run = False

        if command == "wtime":
            go_parameters.wtime = int(param)
        elif command == "btime":
            go_parameters.btime = int(param)
        elif command == "winc":
            go_parameters.winc = int(param)
        elif command == "binc":
            go_parameters.binc = int(param)
        elif command == "movestogo":
            go_parameters.movesToGo = int(param)
        elif command == "depth":
            go_parameters.depth = int(param)
        elif command == "nodes":
            go_parameters.nodes = int(param)
        elif command == "mate":
            go_parameters.mate = int(param)
        elif command == "movetime":
            go_parameters.movetime = int(param)


def go() -> None:
    while True:
        options.flag.wait()
        go_params.reset()
        parse_params(go_params, task.get())
        search_main(go_params, options)
        options.flag.clear()


# MAIN + INITIALIZATIONS
if __name__ == "__main__":
    # do not log unnecessary tensorflow messages
    environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    # disable GPU for model evaluation even if available (slower than cpu for small beast nets)
    environ["CUDA_VISIBLE_DEVICES"] = "-1"

    options = Options()					# global engine options
    go_params = GoParameters()			# parameters for current search
    task = Queue(maxsize=0)				# queue for communication between threads

    worker = Thread(target=go)			# worker thread
    worker.daemon = True				# stop when main thread stops

    print(engineName, "by", author)

    worker.start()
    UciLoop().cmdloop()
