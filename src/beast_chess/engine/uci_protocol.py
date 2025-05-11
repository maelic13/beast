from copy import deepcopy
from multiprocessing import Queue

from beast_chess.infra import Constants, EngineCommand, SearchOptions


class UciProtocol:
    def __init__(self, queue: Queue) -> None:
        self._queue = queue
        self._search_options = SearchOptions()

    def uci_loop(self) -> None:  # noqa: C901
        while True:
            full_command = input().strip().split()
            if not full_command:
                continue
            command = full_command[0]
            args = full_command[1:]

            match command:
                case "uci":
                    (self.uci(),)
                case "isready":
                    (self.is_ready(),)
                case "go":
                    (self.go(args),)
                case "stop":
                    (self.stop(),)
                case "setoption":
                    (self.set_option(args),)
                case "ucinewgame":
                    (self.new_game(),)
                case "position":
                    (self.position(args),)
                case "quit":
                    self.quit()
                    break
                case _:
                    (self.invalid_command(command),)

    def uci(self) -> None:
        """Report information about the engine and available uci options."""
        print(f"id name {Constants.ENGINE_NAME} {Constants.ENGINE_VERSION}")
        print(f"id author {Constants.AUTHOR}")
        for option in self._search_options.get_uci_options():
            print(option)
        print("uciok")

    @staticmethod
    def is_ready() -> None:
        """Report engine readiness."""
        print("readyok")

    def quit(self) -> None:
        """Stop engine process by quit command."""
        self._queue.put(EngineCommand(engine_quit=True))

    def go(self, args: list[str]) -> None:
        """Send go command to the engine with search parameters."""
        self._search_options.set_search_parameters(args)
        self._queue.put(EngineCommand(search_options=deepcopy(self._search_options)))
        self._search_options.reset_temporary_parameters()

    def stop(self) -> None:
        """Stop engine calculation by stop command."""
        self._queue.put(EngineCommand(engine_stop=True))

    def set_option(self, args: list[str]) -> None:
        """Set engine option."""
        self._search_options.set_option(args)

    def new_game(self) -> None:
        """Reset search options for new game."""
        self._search_options.reset()

    def position(self, args: list[str]) -> None:
        """Set new position to search options."""
        self._search_options.set_position(args)

    @staticmethod
    def invalid_command(command: str) -> None:
        """Inform about invalid command."""
        print(f"Invalid command: {command}")
