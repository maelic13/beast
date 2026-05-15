# ruff: noqa: PT009

from __future__ import annotations

import unittest

import chess

from beast_chess.board import STARTING_FEN, Board, uci


def chess_perft(board: chess.Board, depth: int) -> int:
    if depth == 0:
        return 1
    nodes = 0
    for move in board.legal_moves:
        board.push(move)
        nodes += chess_perft(board, depth - 1)
        board.pop()
    return nodes


class BoardMoveGenerationTest(unittest.TestCase):
    def assert_legal_moves_match_python_chess(self, fen: str) -> None:
        board = Board(fen)
        reference = chess.Board(fen)

        actual = sorted(uci(move) for move in board.legal_moves)
        expected = sorted(move.uci() for move in reference.legal_moves)

        self.assertEqual(actual, expected)

    def test_starting_position_perft(self) -> None:
        board = Board()

        self.assertEqual(len(board.legal_moves), 20)
        self.assertEqual(board.perft(1), 20)
        self.assertEqual(board.perft(2), 400)
        self.assertEqual(board.perft(3), 8902)

    def test_legal_moves_match_python_chess_for_tactical_positions(self) -> None:
        for fen in (
            STARTING_FEN,
            "r3k2r/p1ppqpb1/bn2pnp1/2pPN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "8/P6k/8/8/8/8/6Kp/8 w - - 0 1",
            "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
            "rnbq1k1r/pppp1ppp/4pn2/8/1b1PP3/2N2N2/PPP2PPP/R1BQKB1R w KQ - 2 5",
            "8/2p5/3p4/KP5r/8/8/8/7k w - c6 0 1",
            "4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1",
        ):
            with self.subTest(fen=fen):
                self.assert_legal_moves_match_python_chess(fen)

    def test_perft_matches_python_chess_for_rule_edge_cases(self) -> None:
        for fen in (
            "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
            "8/P6k/8/8/8/8/6Kp/8 w - - 0 1",
            "8/2p5/3p4/KP5r/8/8/8/7k w - c6 0 1",
        ):
            with self.subTest(fen=fen):
                board = Board(fen)
                reference = chess.Board(fen)
                self.assertEqual(board.perft(3), chess_perft(reference, 3))

    def test_push_pop_restores_position_and_hash(self) -> None:
        board = Board("r3k2r/p1ppqpb1/bn2pnp1/2pPN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
        original_fen = board.fen()
        original_key = board.zobrist_key

        for move in tuple(board.legal_moves):
            board.push(move)
            board.pop()
            self.assertEqual(board.fen(), original_fen)
            self.assertEqual(board.zobrist_key, original_key)

    def test_push_uci_matches_python_chess_fen(self) -> None:
        board = Board()
        reference = chess.Board()

        for move in ("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"):
            board.push_uci(move)
            reference.push_uci(move)

        self.assertEqual(board.fen(), reference.fen())


if __name__ == "__main__":
    unittest.main()
