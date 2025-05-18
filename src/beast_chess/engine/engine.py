import operator
from collections.abc import Iterable, Iterator
from multiprocessing import Event, Queue
from random import choice
from threading import Timer
from time import time

from chess import PAWN, Board, Move

from beast_chess.heuristics import (
    ClassicalHeuristic,
    Heuristic,
    HeuristicType,
    NeuralNetwork,
    PieceValues,
    RandomHeuristic,
)
from beast_chess.infra import Constants, EngineCommand, SearchOptions


class Engine:
    def __init__(self, queue: Queue) -> None:
        self._heuristic: Heuristic | None = None
        self._nodes_searched = 0
        self._queue = queue
        self._timeout = Event()

    def start(self) -> None:
        """
        Start the engine process, wait for EngineCommand and search for the best move when required.
        """
        while True:
            # check queue for command
            command: EngineCommand = self._queue.get()

            if command.quit:
                break
            if command.stop:
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
            msg = "Time-out."
            raise RuntimeError(msg)

        if self._queue.empty():
            return

        command = self._queue.get_nowait()
        if command.stop or command.quit:
            msg = f"Command: stop - {command.stop}, quit - {command.quit}"
            raise RuntimeError(msg)

    @staticmethod
    def _choose_heuristic(search_options: SearchOptions) -> Heuristic:
        """
        Initialize a heuristic function based on search parameters.
        :param search_options: search parameters
        """
        classical_heuristic = ClassicalHeuristic(
            fifty_moves_rule=search_options.fifty_moves_rule,
            syzygy_path=search_options.syzygy_path,
            syzygy_probe_limit=search_options.syzygy_probe_limit,
        )

        if search_options.heuristic_type == HeuristicType.CLASSICAL:
            return classical_heuristic

        if search_options.heuristic_type == HeuristicType.RANDOM:
            search_options.depth = 1
            return RandomHeuristic()

        if search_options.model_file is None:
            msg = "Warning: incorrect model file."
            raise RuntimeError(msg)

        if search_options.heuristic_type == HeuristicType.NEURAL_NETWORK:
            return NeuralNetwork(
                model_file=search_options.model_file,
                fifty_moves_rule=search_options.fifty_moves_rule,
                syzygy_path=search_options.syzygy_path,
                syzygy_probe_limit=search_options.syzygy_probe_limit,
                threads=search_options.threads,
            )

        return classical_heuristic

    def _start_timer(self, search_options: SearchOptions) -> None:
        """
        Check search options and start the timer if there is limited time for the best move search.
        :param search_options: search parameters
        """
        self._timeout.clear()

        match (
            search_options.board.turn,
            search_options.move_time,
            search_options.white_time,
            search_options.white_increment,
            search_options.black_time,
            search_options.black_increment,
        ):
            case (_, 0, 0, 0, 0, 0):
                return
            case (_, move_time, _, _, _, _) if move_time > 0:
                time_for_move = move_time
            case (True, _, white_time, 0, _, _) if white_time > 0:
                time_for_move = 0.05 * (white_time - Constants.TIME_FLEX)
            case (True, _, white_time, white_increment, _, _) if white_time > 0:
                time_for_move = min(
                    0.1 * white_time + white_increment - Constants.TIME_FLEX,
                    white_time - Constants.TIME_FLEX,
                )
            case (False, _, _, _, black_time, 0) if black_time > 0:
                time_for_move = 0.05 * (black_time - Constants.TIME_FLEX)
            case (False, _, _, _, black_time, black_increment) if black_time > 0:
                time_for_move = min(
                    0.1 * black_time + black_increment - Constants.TIME_FLEX,
                    black_time - Constants.TIME_FLEX,
                )
            case _:
                msg = "Incorrect time options."
                raise RuntimeError(msg)

        timer = Timer(time_for_move / 1000.0, self._timeout.set)
        timer.start()

    def _search(self, board: Board, max_depth: int) -> None:
        """
        Search for the best move and report info to stdout.
        :param board: current board representation
        :param max_depth: limit for depth of iterative search
        """
        # start with a random move choice, to be used in case of timeout before
        # the first depth is reached
        moves: list[Move] = [choice(list(board.legal_moves))]
        depth = 0
        search_started = time() - 0.0001
        self._nodes_searched = 0

        while depth < max_depth:
            depth += 1
            try:
                evaluation, moves = self._negamax(board, depth, float("-inf"), float("inf"))
            except RuntimeError as ex:
                break

            current_time = time() - search_started
            print(
                f"info depth {depth} score cp {int(evaluation)} "
                f"nodes {self._nodes_searched} nps {int(self._nodes_searched / current_time)} "
                f"time {round(1000 * current_time)} "
                f"pv {' '.join([move.uci() for move in moves])}",
                flush=True,
            )

        print(f"bestmove {moves[0].uci()}", flush=True)

    def _negamax(
        self, board: Board, depth: int, alpha: float, beta: float
    ) -> tuple[float, list[Move]]:
        """
        Depth-first search with pruning.
        :param board: chess board representation
        :param depth: allowed depth for deepening
        :param alpha: search parameter alpha
        :param beta: search parameter beta
        :return: evaluation, the best move continuation from the given position
        """
        self._check_stop()
        self._nodes_searched += 1

        if board.is_game_over():
            return self._heuristic.evaluate_result(board, depth), []
        if board.is_repetition() or board.is_fifty_moves():
            return 0.0, []
        if depth == 0:
            return self._quiescence(board, alpha, beta), []

        best_moves: list[Move] = []
        for move in self._order_moves(board, board.legal_moves):
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
        evaluation of position in-between captures or lost after a simple check.
        :param board: chess board representation
        :param alpha: search parameter alpha
        :param beta: search parameter beta
        :return: evaluation
        """
        self._check_stop()

        if board.is_game_over():
            return self._heuristic.evaluate_result(board, -1)
        if board.is_repetition() or board.is_fifty_moves():
            return 0.0

        # heuristic
        evaluation = self._heuristic.evaluate_position(board)

        if evaluation >= beta:
            return beta

        use_delta_pruning = len(board.piece_map()) > 8
        if use_delta_pruning and evaluation < alpha - PieceValues.QUEEN_VALUE:
            return alpha

        alpha = max(alpha, evaluation)

        # expansion and search
        for move in self._get_captures_and_checks(board):
            if use_delta_pruning and board.is_capture(move):
                captured_piece = (
                    PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
                )
                piece_value = PieceValues.as_dict().get(captured_piece) + 200
                if evaluation + piece_value < alpha:
                    continue

            board.push(move)
            score = -self._quiescence(board, -beta, -alpha)
            board.pop()
            self._nodes_searched += 1

            if score >= beta:
                return beta
            alpha = max(alpha, score)

        return alpha

    def _get_captures_and_checks(self, board: Board) -> Iterator[Move]:
        """
        Check for captures and checks for quiescence search.
        :param board: chess board representation
        :return: all moves that either capture a piece or give a check from the current position
        """
        return self._order_moves(
            board,
            iter(
                move
                for move in board.legal_moves
                if board.is_capture(move) or board.gives_check(move)
            ),
        )

    @staticmethod
    def _order_moves(board: Board, moves: Iterable[Move]) -> Iterator[Move]:
        scored_moves: list[tuple[Move, float]] = []
        for move in moves:
            score = 0

            if board.is_capture(move):
                victim_piece = board.piece_at(move.to_square)
                attacker_piece = board.piece_at(move.from_square)
                if victim_piece is not None and attacker_piece is not None:
                    score = PieceValues.as_dict().get(
                        victim_piece.piece_type, 0
                    ) * 10 - PieceValues.as_dict().get(attacker_piece.piece_type, 0)

                if move.promotion:
                    score += PieceValues.as_dict().get(move.promotion, 0) * 5

            if board.gives_check(move):
                score += 1

            scored_moves.append((move, score))

        scored_moves.sort(key=operator.itemgetter(1), reverse=True)
        return iter(x[0] for x in scored_moves)
