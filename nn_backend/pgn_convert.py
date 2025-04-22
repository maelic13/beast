from multiprocessing import Pool, cpu_count, current_process
from time import time

from chess import Board
from chess.engine import Limit, SimpleEngine
from chess.pgn import Game, read_game


class DataHelper:
    _stockfish_path = "stockfish.exe"

    @classmethod
    def parse_pgn_files(cls, game_file_names: list[str]) -> list[str]:
        positions: list[str] = []
        with Pool() as pool:
            for sub_result in pool.map(cls._get_positions, game_file_names):
                positions += sub_result
        return positions

    @classmethod
    def _get_positions(cls, file_name: str) -> list[str]:
        positions: list[str] = []
        num_games = 0
        log_after = 10000
        start_time = time()
        local_start_time = time()
        with open(file_name, encoding="UTF-8") as game_file:
            game = read_game(game_file)
            while game is not None:
                positions += cls._parse_game(game)
                game = read_game(game_file)
                num_games += 1
                if num_games % log_after == 0:
                    cls._log_extracting_progress(
                        file_name,
                        start_time,
                        local_start_time,
                        num_games,
                        log_after,
                        len(positions),
                    )
                    local_start_time = time()
        cls._log_extracting_progress(
            file_name, start_time, local_start_time, num_games, None, len(positions)
        )
        return positions

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
    def evaluate(
        cls, positions: list[str], num_processes: int | None = None
    ) -> list[tuple[str, float]]:
        num_processes = num_processes or cpu_count()
        eval_positions: list[tuple[str, float]] = []
        positions = cls.parse_data(positions, num_processes)

        with Pool(processes=num_processes) as pool:
            for sub_result in pool.map(cls._evaluate_positions, positions):
                eval_positions += sub_result
        return eval_positions

    @classmethod
    def _evaluate_positions(cls, data: list[str]) -> list[tuple[str, float]]:
        log_after = 1000
        start_time = time()
        local_start_time = time()

        analysed_positions: list[tuple[str, float]] = []
        stockfish = SimpleEngine.popen_uci(cls._stockfish_path)
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
        print(f"Globally {int(positions_done / (current_time - start_time))} games/s")
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
    def parse_data(cls, data: list[str], num_processes: int) -> list[list[str]]:
        k, m = divmod(len(data), num_processes)
        return [data[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(num_processes)]

    @classmethod
    def save_evaluated_data_to_file(cls, data: list[tuple[str, float]], file_name: str) -> None:
        with open(file_name, "w", encoding="utf-8") as file:
            file.writelines(f"{item[0]}\t{item[1]}\n" for item in data)

    @classmethod
    def save_positions_to_file(cls, data: list[str], file_name: str) -> None:
        with open(file_name, "w", encoding="utf-8") as file:
            file.writelines(item + "\n" for item in data)


if __name__ == "__main__":
    files = ["databases/games.pgn"]

    start = time()
    extracted_positions = DataHelper.parse_pgn_files(files)
    print(
        f"Extraction took {int((time() - start) / 60)} minutes "
        f"{int((time() - start) % 60)} seconds."
    )
    print(f"Extracted positions: {len(extracted_positions)}.\n")

    start = time()
    extracted_positions = list(set(extracted_positions))
    print(
        f"Elimination of doubles took {int((time() - start) / 60)} minutes "
        f"{int((time() - start) % 60)} seconds."
    )
    print(f"Extracted positions after doubles elimination: {len(extracted_positions)}.\n")

    # start = time()
    # DataHelper.save_positions_to_file(extracted_positions, "positions.txt")
    # print(f"Saving took {int((time() - start) / 60)} minutes "
    #       f"{int((time() - start) % 60)} seconds.\n")

    start = time()
    evaluated_positions = DataHelper.evaluate(extracted_positions)
    print(
        f"Evaluation took {int((time() - start) / 60)} minutes "
        f"{int((time() - start) % 60)} seconds."
    )

    start = time()
    DataHelper.save_evaluated_data_to_file(evaluated_positions, "data/games.txt")
    print(f"Saving took {round(time() - start, 2)} seconds.")
