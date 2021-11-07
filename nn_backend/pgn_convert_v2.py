from multiprocessing import Pool
from time import time
from tqdm import tqdm
from typing import List, Tuple

from chess import Board
from chess.engine import Limit, SimpleEngine
from chess.pgn import Game, read_game


class DataHelper:
    _engines = list()
    _stockfish_path = "D:/Chess/Engines/stockfish.exe"

    @classmethod
    def parse_pgn_files(cls, game_file_names: List[str]) -> List[str]:
        positions: List[str] = list()
        for file_name in game_file_names:
            positions += cls._get_positions(file_name)
        return positions

    @classmethod
    def _get_positions(cls, file_name: str) -> List[str]:
        positions: List[str] = list()
        num_games = 0
        with open(file_name, encoding="UTF-8-SIG") as game_file:
            game = read_game(game_file)
            while game is not None:
                positions += cls._parse_game(game)
                game = read_game(game_file)
                num_games += 1
                print(f"Games extracted from {file_name}: {num_games}")
                print(f"Positions extracted from {file_name}: {len(positions)}")
        return positions

    @staticmethod
    def _parse_game(game: Game) -> List[str]:
        positions: List[str] = list()
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
            positions.append(board.fen())
        return positions

    @classmethod
    def evaluate(cls, positions: List[str]) -> List[Tuple[str, float]]:
        results = list()
        for result in tqdm(Pool().imap_unordered(cls._evaluate_position, positions), total=len(positions)):
            results.append(result)
        return results

    @classmethod
    def _evaluate_position(cls, position: str) -> Tuple[str, float]:
        stockfish = SimpleEngine.popen_uci(cls._stockfish_path)
        score = stockfish.analyse(Board(fen=position), Limit(depth=10))["score"]
        stockfish.close()
        return position, score.relative.wdl().expectation()

    @classmethod
    def save_to_file(cls, data: List[Tuple[str, float]]) -> None:
        with open("evaluated_games.txt", "w") as file:
            for item in data:
                file.write(f"{item[0]}\t{item[1]}\n")


if __name__ == "__main__":
    files = ["human_games.pgn", "iccf_games.pgn"]
    extracted_positions = DataHelper.parse_pgn_files(["mini_test.txt"])
    extracted_positions = list(set(extracted_positions))
    start = time()
    evaluated_positions = DataHelper.evaluate(extracted_positions)
    print(f"Eval took {round(time() - start, 2)} seconds.")
    DataHelper.save_to_file(evaluated_positions)
