from copy import deepcopy
from multiprocessing import Event, Queue
from random import choice
from threading import Timer

from chess import Board, Move

from constants import Constants
from engine_command import EngineCommand
from search_options import SearchOptions


class Engine:
    def __init__(self, queue: Queue) -> None:
        self._queue = queue
        self._timeout: Event = Event()

    def start(self) -> None:
        """
        Start the engine process, wait for EngineCommand and search for best move when required.
        """
        while True:
            # check queue for command
            command: EngineCommand = self._queue.get()

            if command.quit:
                break
            elif command.stop:
                continue

            self._start_timer(command.search_options)
            self._search(command.search_options)

    def _check_stop(self) -> bool:
        """
        Check if stop conditions were met:
            time for calculation is used up
            stop or quit commands received
        :return: stop calculation
        """
        if self._timeout.is_set():
            return True

        if self._queue.empty():
            return False

        command = self._queue.get_nowait()
        return command.stop or command.quit

    def _search(self, search_options: SearchOptions) -> None:
        """
        Search for best move and report info to stdout.
        :param search_options: search parameters
        """
        if self._check_stop():
            return

        print(search_options, flush=True)
        board: Board = deepcopy(search_options.board)
        move: Move = choice(list(board.legal_moves))
        print(f"bestmove {move.uci()}", flush=True)

    def _start_timer(self, search_options: SearchOptions) -> None:
        """
        Check search options and start timer if there is limited time for best move search.
        :param search_options: search parameters
        """
        self._timeout.clear()

        if search_options.depth == float('inf') or not search_options.has_time_options:
            # do not start timer
            return

        time_for_move: int | None = None
        if search_options.movetime != 0:
            time_for_move = (search_options.movetime - Constants.TIME_FLEX) / 1000.
        if search_options.board.turn and search_options.white_time != 0:
            time_for_move = (0.2 * search_options.white_time - Constants.TIME_FLEX) / 1000.
        if not search_options.board.turn and search_options.black_time != 0:
            time_for_move = (0.2 * search_options.black_time - Constants.TIME_FLEX) / 1000.

        if time_for_move is None:
            # wrong time options, do not start timer
            return

        timer = Timer(time_for_move, self._timeout.set)
        timer.start()
