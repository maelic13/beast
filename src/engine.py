from multiprocessing import Queue
from random import choice
from time import time
from threading import Event, Timer

from chess import Board, Move

from engine_command import EngineCommand
from search_options import SearchOptions


class Engine:
    def __init__(self, queue: Queue) -> None:
        self._queue = queue
        self._timeout: Event = Event()

    def start(self) -> None:
        while True:
            command: EngineCommand = self._queue.get()

            if command.quit:
                break
            elif command.stop:
                continue

            self._start_timer()
            self._search(command.search_options)

    def _search(self, search_options: SearchOptions) -> None:
        if self._check_stop():
            return

        print(search_options, flush=True)
        board: Board = self._get_current_board(search_options.fen, search_options.played_moves)
        move: Move = choice(list(board.legal_moves))
        print(f"bestmove {move.uci()}", flush=True)

    def _check_stop(self) -> bool:
        if self._timeout.is_set():
            return True

        if self._queue.empty():
            return False

        command = self._queue.get_nowait()
        return command.stop or command.quit

    @staticmethod
    def _get_current_board(fen: str, played_moves: list[str]) -> Board:
        board = Board(fen)
        for move in played_moves:
            board.push_uci(move)
        return board

    def _start_timer(self) -> None:
        self._timeout.clear()
        time_for_move = 1.
        timer = Timer(time_for_move, self._timeout.set)
        timer.start()
