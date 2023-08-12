from copy import deepcopy
from multiprocessing import Queue

from constants import Constants
from engine_command import EngineCommand
from search_options import SearchOptions


class UciProtocol:
    def __init__(self, queue: Queue) -> None:
        self._queue = queue
        self._search_options = SearchOptions()

    def uci_loop(self) -> None:
        while True:
            full_command = input().strip().split()
            if not full_command:
                continue
            command = full_command[0]
            args = full_command[1:]

            match command:
                case "uci": self.uci(),
                case "isready": self.isready(),
                case "go": self.go(args),
                case "stop": self.stop(),
                case "setoption": self.setoption(args),
                case "ucinewgame": self.ucinewgame(),
                case "position": self.position(args),
                case "quit":
                    self.quit()
                    break
                case _: continue

    @staticmethod
    def uci() -> None:
        """ Report information about the engine and available uci options. """
        print(f"id name {Constants.ENGINE_NAME} {Constants.ENGINE_VERSION}")
        print(f"id author {Constants.AUTHOR}")
        print("uciok")

    @staticmethod
    def isready() -> None:
        """ Report engine readiness. """
        print("readyok")

    def quit(self) -> None:
        """ Stop engine process by quit command. """
        self._queue.put(EngineCommand(engine_quit=True))

    def go(self, args: list[str]) -> None:
        """ Send go command to the engine with search parameters. """
        self._search_options.set_search_parameters(args)
        self._queue.put(EngineCommand(search_options=deepcopy(self._search_options)))

    def stop(self) -> None:
        """ Stop engine calculation by stop command. """
        self._queue.put(EngineCommand(engine_stop=True))

    @staticmethod
    def setoption(_args: list[str]) -> None:
        """ Set engine option. """
        print("No engine options currently supported.")

    def ucinewgame(self):
        """ Reset search options for new game. """
        self._search_options.reset()

    def position(self, args: list[str]) -> None:
        """ Set new position to search options. """
        self._search_options.set_position(args)
