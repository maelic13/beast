from __future__ import annotations

# ruff: noqa: PT009
import unittest
from queue import Queue

from beast_chess.board import Board, uci
from beast_chess.engine.engine import Engine
from beast_chess.heuristics import ClassicalHeuristic


class EngineSearchTest(unittest.TestCase):
    def test_search_restores_board_and_returns_legal_pv(self) -> None:
        board = Board()
        original_fen = board.fen()
        engine = self._engine()

        _score, pv = engine._negamax(board, 2, float("-inf"), float("inf"))  # noqa: SLF001

        self.assertEqual(board.fen(), original_fen)
        self.assertTrue(pv)
        self.assertTrue(board.is_legal(pv[0]))

    def test_search_finds_mate_in_one(self) -> None:
        board = Board("7k/8/5KQ1/8/8/8/8/8 w - - 0 1")
        engine = self._engine()

        score, pv = engine._negamax(board, 1, float("-inf"), float("inf"))  # noqa: SLF001

        self.assertGreater(score, 300_000)
        self.assertEqual([uci(move) for move in pv], ["g6g7"])

    @staticmethod
    def _engine() -> Engine:
        engine = Engine(Queue())
        engine._heuristic = ClassicalHeuristic()  # noqa: SLF001
        engine._reset_search_tables()  # noqa: SLF001
        return engine


if __name__ == "__main__":
    unittest.main()
