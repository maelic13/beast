from multiprocessing import Event, Queue
from random import choice
from threading import Timer
from time import time

from chess import Board, Move, PAWN

from constants import Constants
from engine_command import EngineCommand
from heuristic import ClassicalHeuristic, Heuristic, HeuristicType, PieceValues, RandomHeuristic
from search_options import SearchOptions


class Engine:
    def __init__(self, queue: Queue) -> None:
        self._heuristic: Heuristic | None = None
        self._nodes_searched = 0
        self._queue = queue
        self._timeout = Event()

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

            self._heuristic = self._choose_heuristic(command.search_options)
            self._start_timer(command.search_options)
            self._search(command.search_options.board, command.search_options.depth)

    def _check_stop(self) -> None:
        """
        Check if stop conditions were met:
            time for calculation is used up
            stop or quit commands received
        :raise RuntimeError: stop calculation
        """
        if self._timeout.is_set():
            raise RuntimeError("Time-out.")

        if self._queue.empty():
            return

        command = self._queue.get_nowait()
        if command.stop or command.quit:
            raise RuntimeError(f"Command: stop - {command.stop}, quit - {command.quit}")

    @staticmethod
    def _choose_heuristic(search_options: SearchOptions) -> Heuristic:
        """
        Initialize heuristic function based on search parameters.
        :param search_options: search parameters
        """
        classical_heuristic = ClassicalHeuristic(
            fifty_moves_rule=search_options.fifty_moves_rule,
            syzygy_path=search_options.syzygy_path,
            syzygy_probe_limit=search_options.syzygy_probe_limit)

        if search_options.heuristic_type == HeuristicType.CLASSICAL:
            return classical_heuristic

        if search_options.heuristic_type == HeuristicType.RANDOM:
            search_options.depth = 1
            return RandomHeuristic()

        return classical_heuristic

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
        moves: list[Move] = [choice(list(board.legal_moves))]
        depth = 0
        search_started = time() - 0.0001
        self._nodes_searched = 0

        while depth < max_depth:
            depth += 1
            try:
                evaluation, moves = self._negamax(board, depth, float('-inf'), float('inf'))
            except RuntimeError:
                break

            current_time = time() - search_started
            print(f"info depth {depth} score cp {evaluation} "
                  f"nodes {self._nodes_searched} nps {int(self._nodes_searched / current_time)} "
                  f"time {round(1000 * current_time)} "
                  f"pv {' '.join([move.uci() for move in moves])}", flush=True)

        print(f"bestmove {moves[0].uci()}", flush=True)

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
        self._check_stop()
        self._nodes_searched += 1

        if board.is_game_over() or depth == 0 and not self._heuristic.use_quiescence():
            return self._heuristic.evaluate(board), []
        if depth == 0 and self._heuristic.use_quiescence():
            return self._quiescence(board, alpha, beta), []

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

    def _quiescence(self, board: Board, alpha: float, beta: float) -> float:
        """
        Quiescence search checks all possible captures and checks to ensure not returning
        evaluation of position in-between captures or lost after simple check.
        :param board: chess board representation
        :param alpha: search parameter alpha
        :param beta: search parameter beta
        :return: evaluation
        """
        self._check_stop()

        # heuristic
        evaluation = self._heuristic.evaluate(board)

        if evaluation >= beta:
            return beta

        use_delta_pruning = len(board.piece_map()) > 8
        if use_delta_pruning:
            if evaluation < alpha - 1000:
                return alpha

        if evaluation > alpha:
            alpha = evaluation

        # expansion and search
        for move in self._get_captures_and_checks(board):
            if use_delta_pruning and board.is_capture(move):
                captured_piece = (
                    PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square))
                piece_value = PieceValues.as_dict().get(captured_piece) + 200
                if evaluation + piece_value < alpha:
                    continue

            board.push(move)
            score = -self._quiescence(board, -beta, -alpha)
            board.pop()
            self._nodes_searched += 1

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    @staticmethod
    def _get_captures_and_checks(board: Board) -> list[Move]:
        """
        Check for captures and checks for quiescence search.
        :param board: chess board representation
        :return: all moves that either capture a piece, or give check from current position
        """
        # TODO: move ordering to get best results
        return [move for move in board.legal_moves
                if board.is_capture(move) or board.gives_check(move)]
