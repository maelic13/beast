from multiprocessing import Event, Queue
from random import choice
from threading import Timer
from time import time

from chess import Board, Move

from classical_heuristic import ClassicalHeuristic
from constants import Constants
from engine_command import EngineCommand
from search_options import SearchOptions


class Engine:
    def __init__(self, queue: Queue) -> None:
        self._heuristic = None
        self._nodes_searched = 0
        self._queue = queue
        self._stop = False
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

            self._initialize_heuristic(command.search_options)
            self._start_timer(command.search_options)
            self._search(command.search_options.board, command.search_options.depth)

    def _check_stop(self) -> bool:
        """
        Check if stop conditions were met:
            time for calculation is used up
            stop or quit commands received
        :return: stop calculation
        """
        if self._timeout.is_set():
            self._stop = True
            return self._stop

        if self._queue.empty():
            return self._stop

        command = self._queue.get_nowait()
        self._stop = command.stop or command.quit
        return self._stop

    def _initialize_heuristic(self, search_options: SearchOptions) -> None:
        """
        Initialize heuristic function based on search parameters.
        :param search_options: search parameters
        """
        self._heuristic = ClassicalHeuristic(search_options)

    def _start_timer(self, search_options: SearchOptions) -> None:
        """
        Check search options and start timer if there is limited time for best move search.
        :param search_options: search parameters
        """
        self._timeout.clear()

        if not search_options.has_time_options:
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

    def _search(self, board: Board, max_depth: float) -> None:
        """
        Search for best move and report info to stdout.
        :param board: current board representation
        :param max_depth: limit for depth of iterative search
        """
        # start with random move choice, to be used in case of timeout before first depth is reached
        best_moves: list[Move] = [choice(list(board.legal_moves))]
        depth = 0
        search_started = time() - 0.0001
        self._nodes_searched = 0
        self._stop = False

        while depth < max_depth and not self._check_stop():
            depth += 1
            evaluation, moves = self._negamax(board, depth, float('-inf'), float('inf'))
            if self._stop:
                continue

            best_moves = moves
            current_time = time() - search_started
            print(f"info depth {depth} score cp {evaluation} "
                  f"nodes {self._nodes_searched} nps {int(self._nodes_searched / current_time)} "
                  f"time {round(1000 * current_time)} "
                  f"pv {' '.join([move.uci() for move in best_moves])}", flush=True)

        print(f"bestmove {best_moves[0].uci()}", flush=True)

    def _negamax(self, board: Board, depth: float, alpha: float, beta: float
                 ) -> tuple[float, list[Move]]:
        """
        Depth first search with pruning.
        :param board: chess board representation
        :param depth: allowed depth for deepening
        :param alpha: search parameter alpha
        :param beta: search parameter beta
        :return: evaluation, best move continuation from given position
        """
        if self._check_stop():
            return 0., []

        self._nodes_searched += 1
        if depth == 0 or board.is_game_over():
            return self._heuristic.evaluate(board), []

        best_moves: list[Move] = []
        for move in board.legal_moves:
            board.push(move)
            evaluation, moves = self._negamax(board, depth - 1, -beta, -alpha)
            board.pop()

            evaluation *= -1
            moves.insert(0, move)

            if evaluation >= beta:
                return beta, []
            if evaluation > alpha:
                alpha = evaluation
                best_moves = moves

        return alpha, best_moves
