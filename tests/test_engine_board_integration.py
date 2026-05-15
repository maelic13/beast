# ruff: noqa: PT009

from __future__ import annotations

import unittest

from beast_chess.board import Board
from beast_chess.heuristics import ClassicalHeuristic
from beast_chess.infra import SearchOptions


class EngineBoardIntegrationTest(unittest.TestCase):
    def test_search_options_use_new_board_and_do_not_expose_syzygy_options(self) -> None:
        options = SearchOptions()

        self.assertIsInstance(options.board, Board)
        self.assertFalse(
            any("syzygy" in option.lower() for option in SearchOptions.get_uci_options())
        )

    def test_position_parsing_uses_new_board_move_stack(self) -> None:
        options = SearchOptions()

        options.set_position(["startpos", "moves", "e2e4", "e7e5"])

        self.assertIsInstance(options.board, Board)
        self.assertEqual(
            options.board.fen(),
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
        )

    def test_classical_heuristic_evaluates_new_board(self) -> None:
        heuristic = ClassicalHeuristic()

        self.assertEqual(heuristic.evaluate_position(Board()), 0)


if __name__ == "__main__":
    unittest.main()
