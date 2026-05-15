# ruff: noqa: PT009

from __future__ import annotations

import unittest

from beast_chess.board import STARTING_FEN, Board, uci

LEGAL_MOVE_FIXTURES: dict[str, tuple[str, ...]] = {
    STARTING_FEN: (
        "a2a3",
        "a2a4",
        "b1a3",
        "b1c3",
        "b2b3",
        "b2b4",
        "c2c3",
        "c2c4",
        "d2d3",
        "d2d4",
        "e2e3",
        "e2e4",
        "f2f3",
        "f2f4",
        "g1f3",
        "g1h3",
        "g2g3",
        "g2g4",
        "h2h3",
        "h2h4",
    ),
    "r3k2r/p1ppqpb1/bn2pnp1/2pPN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1": (
        "a1b1",
        "a1c1",
        "a1d1",
        "a2a3",
        "a2a4",
        "b2b3",
        "c3a4",
        "c3b1",
        "c3b5",
        "c3d1",
        "d2c1",
        "d2e3",
        "d2f4",
        "d2g5",
        "d2h6",
        "d5d6",
        "d5e6",
        "e1c1",
        "e1d1",
        "e1f1",
        "e1g1",
        "e2a6",
        "e2b5",
        "e2c4",
        "e2d1",
        "e2d3",
        "e2f1",
        "e5c4",
        "e5c6",
        "e5d3",
        "e5d7",
        "e5f7",
        "e5g4",
        "e5g6",
        "f3d3",
        "f3e3",
        "f3f4",
        "f3f5",
        "f3f6",
        "f3g3",
        "f3g4",
        "f3h3",
        "f3h5",
        "g2g3",
        "g2g4",
        "g2h3",
        "h1f1",
        "h1g1",
    ),
    "8/P6k/8/8/8/8/6Kp/8 w - - 0 1": (
        "a7a8b",
        "a7a8n",
        "a7a8q",
        "a7a8r",
        "g2f1",
        "g2f2",
        "g2f3",
        "g2g3",
        "g2h1",
        "g2h2",
        "g2h3",
    ),
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1": (
        "a1a2",
        "a1a3",
        "a1a4",
        "a1a5",
        "a1a6",
        "a1a7",
        "a1a8",
        "a1b1",
        "a1c1",
        "a1d1",
        "e1c1",
        "e1d1",
        "e1d2",
        "e1e2",
        "e1f1",
        "e1f2",
        "e1g1",
        "h1f1",
        "h1g1",
        "h1h2",
        "h1h3",
        "h1h4",
        "h1h5",
        "h1h6",
        "h1h7",
        "h1h8",
    ),
    "rnbq1k1r/pppp1ppp/4pn2/8/1b1PP3/2N2N2/PPP2PPP/R1BQKB1R w KQ - 2 5": (
        "a1b1",
        "a2a3",
        "a2a4",
        "b2b3",
        "c1d2",
        "c1e3",
        "c1f4",
        "c1g5",
        "c1h6",
        "d1d2",
        "d1d3",
        "d1e2",
        "d4d5",
        "e1d2",
        "e1e2",
        "e4e5",
        "f1a6",
        "f1b5",
        "f1c4",
        "f1d3",
        "f1e2",
        "f3d2",
        "f3e5",
        "f3g1",
        "f3g5",
        "f3h4",
        "g2g3",
        "g2g4",
        "h1g1",
        "h2h3",
        "h2h4",
    ),
    "8/2p5/3p4/KP5r/8/8/8/7k w - c6 0 1": (
        "a5a4",
        "a5a6",
        "a5b4",
    ),
    "4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1": (
        "d4d3",
        "d4e3",
        "e8d7",
        "e8d8",
        "e8e7",
        "e8f7",
        "e8f8",
    ),
}

PERFT_3_FIXTURES = {
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1": 13744,
    "8/P6k/8/8/8/8/6Kp/8 w - - 0 1": 883,
    "8/2p5/3p4/KP5r/8/8/8/7k w - c6 0 1": 275,
}


class BoardMoveGenerationTest(unittest.TestCase):
    def assert_legal_moves_match_fixture(self, fen: str) -> None:
        board = Board(fen)

        actual = sorted(uci(move) for move in board.generate_legal_moves())
        expected = sorted(LEGAL_MOVE_FIXTURES[fen])

        self.assertEqual(actual, expected)

    def test_starting_position_perft(self) -> None:
        board = Board()

        self.assertEqual(len(board.generate_legal_moves()), 20)
        self.assertEqual(board.perft(1), 20)
        self.assertEqual(board.perft(2), 400)
        self.assertEqual(board.perft(3), 8902)

    def test_legal_moves_match_fixtures_for_tactical_positions(self) -> None:
        for fen in LEGAL_MOVE_FIXTURES:
            with self.subTest(fen=fen):
                self.assert_legal_moves_match_fixture(fen)

    def test_perft_matches_rule_edge_case_fixtures(self) -> None:
        for fen, expected_nodes in PERFT_3_FIXTURES.items():
            with self.subTest(fen=fen):
                board = Board(fen)
                self.assertEqual(board.perft(3), expected_nodes)

    def test_push_pop_restores_position_and_hash(self) -> None:
        board = Board("r3k2r/p1ppqpb1/bn2pnp1/2pPN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        original_fen = board.fen()
        original_key = board.zobrist_key

        for move in tuple(board.generate_legal_moves()):
            board.push(move)
            board.pop()
            self.assertEqual(board.fen(), original_fen)
            self.assertEqual(board.zobrist_key, original_key)

    def test_push_uci_matches_expected_fen(self) -> None:
        board = Board()

        for move in ("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"):
            board.push_uci(move)

        self.assertEqual(
            board.fen(),
            "r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4",
        )


if __name__ == "__main__":
    unittest.main()
