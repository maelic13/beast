# ruff: noqa: PT009, SLF001

from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO
from queue import Queue

from beast_chess.board import Board, uci
from beast_chess.engine.engine import Engine
from beast_chess.engine.uci_protocol import UciProtocol
from beast_chess.heuristics import ClassicalHeuristic


class BoardPlayUseCaseTest(unittest.TestCase):
    def test_opening_line_can_castle_update_state_and_rewind_cleanly(self) -> None:
        board = Board()
        original_fen = board.fen()
        original_key = board.zobrist_key

        played_moves = (
            "e2e4",
            "e7e5",
            "g1f3",
            "b8c6",
            "f1b5",
            "a7a6",
            "e1g1",
            "g8f6",
            "f1e1",
        )
        for move in played_moves:
            legal_moves = {uci(legal_move) for legal_move in board.generate_legal_moves()}
            self.assertIn(move, legal_moves)
            board.push_uci(move)

        self.assertEqual(
            board.fen(),
            "r1bqkb1r/1ppp1ppp/p1n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQR1K1 b kq - 3 5",
        )
        self.assertFalse(board.is_check())

        rewound_moves = []
        while board.move_stack:
            rewound_moves.append(uci(board.pop()))

        self.assertEqual(tuple(rewound_moves), tuple(reversed(played_moves)))
        self.assertEqual(board.fen(), original_fen)
        self.assertEqual(board.zobrist_key, original_key)

    def test_pawn_tactics_expose_search_relevant_moves_and_rewind_cleanly(self) -> None:
        board = Board("8/P6k/8/8/8/8/6Kp/8 w - - 0 1")
        original_fen = board.fen()
        original_key = board.zobrist_key
        promotion_moves = {"a7a8q", "a7a8r", "a7a8b", "a7a8n"}

        legal_moves = {uci(move) for move in board.generate_legal_moves()}
        tactical_moves = {uci(move) for move in board.generate_legal_captures()}

        self.assertLessEqual(promotion_moves, legal_moves)
        self.assertLessEqual(promotion_moves, tactical_moves)

        board.push_uci("a7a8q")
        self.assertEqual(board.fen(), "Q7/7k/8/8/8/8/6Kp/8 b - - 0 1")
        self.assertEqual(uci(board.pop()), "a7a8q")
        self.assertEqual(board.fen(), original_fen)
        self.assertEqual(board.zobrist_key, original_key)

    def test_en_passant_is_allowed_when_safe_and_rejected_when_it_exposes_king(self) -> None:
        safe_capture = Board("8/8/8/3pP3/8/8/8/4K2k w - d6 0 1")
        original_fen = safe_capture.fen()
        original_key = safe_capture.zobrist_key

        self.assertIn("e5d6", {uci(move) for move in safe_capture.generate_legal_moves()})
        safe_capture.push_uci("e5d6")
        self.assertEqual(safe_capture.fen(), "8/8/3P4/8/8/8/8/4K2k b - - 0 1")
        safe_capture.pop()
        self.assertEqual(safe_capture.fen(), original_fen)
        self.assertEqual(safe_capture.zobrist_key, original_key)

        pinned_capture = Board("8/2p5/3p4/KP5r/8/8/8/7k w - c6 0 1")
        legal_moves = {uci(move) for move in pinned_capture.generate_legal_moves()}

        self.assertNotIn("b5c6", legal_moves)
        self.assertEqual(legal_moves, {"a5a4", "a5a6", "a5b4"})


class EngineUseCaseTest(unittest.TestCase):
    def test_repeated_position_is_scored_as_draw_without_disturbing_history(self) -> None:
        board = Board()
        repeated_line = (
            "g1f3",
            "g8f6",
            "f3g1",
            "f6g8",
            "g1f3",
            "g8f6",
            "f3g1",
            "f6g8",
        )
        for move in repeated_line:
            board.push_uci(move)
        original_fen = board.fen()
        original_key = board.zobrist_key

        score, pv = self._engine()._negamax(board, 3, float("-inf"), float("inf"))

        self.assertTrue(board.is_repetition())
        self.assertEqual(score, 0.0)
        self.assertEqual(pv, [])
        self.assertEqual(board.fen(), original_fen)
        self.assertEqual(board.zobrist_key, original_key)

    def test_iterative_search_reports_mating_bestmove_and_preserves_position(self) -> None:
        board = Board("7k/8/5KQ1/8/8/8/8/8 w - - 0 1")
        original_fen = board.fen()
        engine = self._engine()
        output = StringIO()

        with redirect_stdout(output):
            engine._search(board, 1)

        self.assertIn("info depth 1", output.getvalue())
        self.assertIn("pv g6g7", output.getvalue())
        self.assertIn("bestmove g6g7", output.getvalue())
        self.assertEqual(board.fen(), original_fen)

    def test_uci_session_queues_search_stop_newgame_and_quit_commands(self) -> None:
        queue: Queue = Queue()
        protocol = UciProtocol(queue)
        output = StringIO()

        with redirect_stdout(output):
            protocol.uci()
            protocol.is_ready()

        self.assertIn("id name Beast 4.0.0", output.getvalue())
        self.assertIn("option name Heuristic type", output.getvalue())
        self.assertIn("uciok", output.getvalue())
        self.assertIn("readyok", output.getvalue())

        protocol.position(["startpos", "moves", "e2e4", "e7e5", "g1f3"])
        protocol.go(["depth", "2"])
        search_command = queue.get_nowait()

        self.assertEqual(search_command.search_options.depth, 2)
        self.assertEqual(
            search_command.search_options.board.fen(),
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
        )

        protocol.stop()
        protocol.new_game()
        protocol.quit()

        self.assertTrue(queue.get_nowait().stop)
        self.assertTrue(queue.get_nowait().new_game)
        self.assertTrue(queue.get_nowait().quit)

    @staticmethod
    def _engine() -> Engine:
        engine = Engine(Queue())
        engine._heuristic = ClassicalHeuristic()
        engine._reset_search_tables()
        return engine


if __name__ == "__main__":
    unittest.main()
