from collections.abc import Callable
from functools import partial
from multiprocessing import Pool, cpu_count, current_process
from pathlib import Path
from time import time
from typing import Any

import numpy as np
from chess import Board
from chess.engine import Limit, SimpleEngine
from chess.pgn import Game, read_game


class PgnConverter:
    @classmethod
    def parse_pgn_files(cls, pgn_files: list[Path]) -> list[str]:
        positions: list[str] = []
        num_games = 0
        log_after = 10000
        start_time = time()
        local_start_time = time()
        for pgn_file in pgn_files:
            with open(pgn_file, encoding="UTF-8") as file:
                game = read_game(file)
                while game is not None:
                    positions += cls._parse_game(game)
                    game = read_game(file)
                    num_games += 1
                    if num_games % log_after == 0:
                        cls._log_extracting_progress(
                            pgn_file.name,
                            start_time,
                            local_start_time,
                            num_games,
                            log_after,
                            len(positions),
                        )
                        local_start_time = time()
            cls._log_extracting_progress(
                pgn_file.name, start_time, local_start_time, num_games, None, len(positions)
            )

        print(
            f"Extraction took {int((time() - start_time) / 60)} minutes "
            f"{int((time() - start_time) % 60)} seconds."
        )
        print(f"Extracted positions: {len(positions)}.\n")

        start_time = time()
        positions = list(set(positions))
        print(
            f"Elimination of doubles took {int((time() - start_time) / 60)} minutes "
            f"{int((time() - start_time) % 60)} seconds."
        )
        print(f"Extracted positions after doubles elimination: {len(positions)}.\n")

        return positions

    @classmethod
    def evaluate_positions(
        cls, positions: list[str], stockfish_path: Path, num_processes: int | None = None
    ) -> list[tuple[str, float]]:
        num_processes = num_processes or cpu_count()
        eval_positions: list[tuple[str, float]] = []
        positions = cls._parse_data(positions, num_processes)

        evaluate_with_path = partial(cls._evaluate_positions, stockfish_path=stockfish_path)

        with Pool(processes=num_processes) as pool:
            for sub_result in pool.imap(evaluate_with_path, positions):
                eval_positions += sub_result
        return eval_positions

    @classmethod
    def save_evaluated_data_to_file(cls, data: list[tuple[str, float]], file_path: Path) -> None:
        print(f"Saving positions to {file_path}...")
        start = time()
        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(f"{item[0]}\t{item[1]}\n" for item in data)
        print(f"Saving took {int(time() - start)} seconds.")

    @classmethod
    def load_evaluated_positions_from_file(cls, file_path: Path) -> tuple[list[str], list[float]]:
        print(f"Loading positions and evaluations from {file_path}...")

        start = time()
        positions: list[str] = []
        evaluations: list[float] = []
        with open(file_path, encoding="utf-8") as file:
            for line in file:
                position, evaluation = line.strip().split("\t")
                positions.append(position)
                evaluations.append(float(evaluation))

        print(f"Loading took {int(time() - start)} seconds.")
        print(f"Loaded {len(positions)} positions and evaluations.")
        return positions, evaluations

    @classmethod
    def save_positions_to_file(cls, data: list[str], file_path: Path) -> None:
        print(f"Saving positions to {file_path}...")
        start = time()
        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(item + "\n" for item in data)
        print(f"Saving took {int(time() - start)} seconds.")

    @classmethod
    def load_positions_from_file(cls, file_path: Path) -> list[str]:
        print(f"Loading positions from {file_path}...")
        start = time()
        with open(file_path, encoding="utf-8") as file:
            positions = [line.strip() for line in file]
        print(f"Loading took {int(time() - start)} seconds.")
        print(f"Loaded {len(positions)} positions.")
        return positions

    @classmethod
    def load_training_data_from_file(
        cls, file_path: Path, get_input: Callable[[str], Any]
    ) -> tuple[np.ndarray, np.ndarray]:
        print(f"Loading training data from {file_path}...")
        start = time()

        with open(file_path, encoding="utf-8") as file:
            line_count = sum(1 for _ in file)

        with open(file_path, encoding="utf-8") as file:
            first_line = file.readline().strip()
            fen = first_line.strip().split("\t")[0]
            input_shape = get_input(fen).shape

        inputs = np.empty((line_count, *input_shape), dtype=np.float32)
        evaluations = np.empty(line_count, dtype=np.float32)

        with open(file_path, encoding="utf-8") as file:
            for i, line in enumerate(file):
                position, evaluation = line.strip().split("\t")
                inputs[i] = get_input(position)
                evaluations[i] = float(evaluation)

        print(f"Loading took {int(time() - start)} seconds.")
        print(f"Loaded {len(evaluations)} training data.")
        return inputs, evaluations

    @classmethod
    def _log_extracting_progress(
        cls,
        file_name: str,
        start_time: float,
        local_start_time: float,
        games_number: int,
        log_games_number: int | None,
        positions_number: int,
    ) -> None:
        current_time = time()
        seconds = int((current_time - start_time) % 60)
        minutes = int((current_time - start_time) / 60)
        print(file_name)
        print(f"{games_number} games analysed, {positions_number} positions extracted.")
        print(f"{minutes} minutes {seconds} seconds elapsed.")
        if log_games_number:
            print(f"Currently {int(log_games_number / (current_time - local_start_time))} games/s")
        print(f"Globally {int(games_number / (current_time - start_time))} games/s")
        print()

    @staticmethod
    def _parse_game(game: Game) -> list[str]:
        positions: list[str] = []
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
            positions.append(board.fen())
        return positions

    @classmethod
    def _evaluate_positions(cls, data: list[str], stockfish_path: Path) -> list[tuple[str, float]]:
        log_after = 1000
        start_time = time()
        local_start_time = time()

        analysed_positions: list[tuple[str, float]] = []
        stockfish = SimpleEngine.popen_uci(str(stockfish_path))
        for position in data:
            score = stockfish.analyse(Board(fen=position), Limit(depth=10))["score"]
            analysed_positions.append((position, score.relative.wdl().expectation()))
            if len(analysed_positions) % log_after == 0:
                cls._log_evaluating_progress(
                    f"{current_process().name}",
                    start_time,
                    local_start_time,
                    len(analysed_positions),
                    log_after,
                    len(data),
                )
                local_start_time = time()
        stockfish.close()
        return analysed_positions

    @classmethod
    def _log_evaluating_progress(
        cls,
        process_name: str,
        start_time: float,
        local_start_time: float,
        positions_done: int,
        log_after: int | None,
        total_positions: int,
    ) -> None:
        current_time = time()
        minutes = int((current_time - start_time) / 60)
        seconds = int((current_time - start_time) % 60)
        print(process_name)
        print(f"{positions_done}/{total_positions} positions evaluated.")
        print(f"{minutes} minutes {seconds} seconds elapsed.")
        if log_after:
            speed = int(log_after / (current_time - local_start_time))
            print(f"Currently {speed} positions/s")
        print(f"Globally {int(positions_done / (current_time - start_time))} positions/s")
        total_seconds_left = (total_positions - positions_done) / (
            int(log_after / (current_time - local_start_time))
        )
        hours_left = int(total_seconds_left / 3600)
        minutes_left = int((total_seconds_left % 3600) / 60)
        seconds_left = int(total_seconds_left % 60)
        print(
            f"Expected time left: {hours_left} hours {minutes_left} minutes {seconds_left} seconds."
        )
        print()

    @classmethod
    def _parse_data(cls, data: list[str], num_processes: int) -> list[list[str]]:
        k, m = divmod(len(data), num_processes)
        return [data[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(num_processes)]
