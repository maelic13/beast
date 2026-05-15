# ruff: noqa: PT009
"""Board performance benchmarks — mirrors beast2's test_board_performance.py.

Tests the operations that dominate a chess engine's search loop:
  1. Legal move generation  — called at every search node
  2. Capture generation     — quiescence search hot-path
  3. Make/unmake             — tree traversal (push/pop)
  4. Check detection         — check extensions, mate detection
  5. Perft(4) startpos       — end-to-end pipeline throughput
  6. Game simulation         — realistic 2-ply search-like traversal
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING

from beast_chess.board import STARTING_FEN, Board

if TYPE_CHECKING:
    from collections.abc import Callable

# Positions spanning opening → middlegame → endgame with varied characteristics
BENCHMARK_FENS = (
    STARTING_FEN,
    # Kiwipete: complex middlegame, many captures/pins/checks
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    # Middlegame with some tension
    "rnbq1k1r/pppp1ppp/4pn2/8/1b1PP3/2N2N2/PPP2PPP/R1BQKB1R w KQ - 2 5",
    # Sparse endgame
    "8/2p5/3p4/KP5r/8/8/8/7k w - c6 0 1",
    # Position with side-to-move in check (common in search)
    "rnbqkb1r/pppp1ppp/5n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 3 3",
)


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    label: str
    operations: int
    seconds: float
    operations_per_second: float


class BoardPerformanceTest(unittest.TestCase):
    def test_engine_core_operations_have_reasonable_throughput(self) -> None:
        boards = tuple(Board(fen) for fen in BENCHMARK_FENS)

        results = (
            self._benchmark(
                "legal moves",
                lambda: self._legal_moves(boards),
                200,
            ),
            self._benchmark(
                "captures",
                lambda: self._capture_gen(boards),
                500,
            ),
            self._benchmark(
                "make/unmake",
                lambda: self._make_unmake(boards),
                100,
            ),
            self._benchmark(
                "check detection",
                lambda: self._check_detection(boards),
                2_000,
            ),
            self._benchmark(
                "perft(4) startpos",
                lambda: Board().perft(4),
                3,
                warmups=1,
            ),
            self._benchmark(
                "game simulation",
                lambda: self._game_simulation(boards),
                20,
                warmups=3,
            ),
        )

        print()
        print("Board performance")
        print("-" * 65)
        for result in results:
            print(
                f"{result.label:20} "
                f"{result.operations_per_second:>12,.0f} ops/s "
                f"({result.operations:>9,} ops in {result.seconds:.3f}s)"
            )

        # Minimum viable thresholds (should not regress below these)
        self.assertGreaterEqual(results[0].operations_per_second, 50_000)  # legal
        self.assertGreaterEqual(results[1].operations_per_second, 50_000)  # captures
        self.assertGreaterEqual(results[2].operations_per_second, 10_000)  # make/unmake
        self.assertGreaterEqual(results[3].operations_per_second, 200_000)  # check detect
        self.assertGreaterEqual(results[4].operations_per_second, 20_000)  # perft
        self.assertGreaterEqual(results[5].operations_per_second, 5_000)  # game sim

    # ------------------------------------------------------------------
    # Harness
    # ------------------------------------------------------------------

    @staticmethod
    def _benchmark(
        label: str,
        workload: Callable[[], int],
        iterations: int,
        *,
        warmups: int = 10,
    ) -> BenchmarkResult:
        for _ in range(warmups):
            workload()

        best_seconds = float("inf")
        best_operations = 0
        for _ in range(3):
            operations = 0
            started = perf_counter()
            for _ in range(iterations):
                operations += workload()
            elapsed = perf_counter() - started
            if elapsed < best_seconds:
                best_seconds = elapsed
                best_operations = operations

        return BenchmarkResult(
            label=label,
            operations=best_operations,
            seconds=best_seconds,
            operations_per_second=best_operations / best_seconds,
        )

    # ------------------------------------------------------------------
    # Workloads
    # ------------------------------------------------------------------

    @staticmethod
    def _legal_moves(boards: tuple[Board, ...]) -> int:
        return sum(len(b.generate_legal_moves()) for b in boards)

    @staticmethod
    def _capture_gen(boards: tuple[Board, ...]) -> int:
        return sum(len(b.generate_legal_captures()) for b in boards)

    @staticmethod
    def _make_unmake(boards: tuple[Board, ...]) -> int:
        ops = 0
        for board in boards:
            for move in board.generate_legal_moves():
                board.push(move)
                board.pop()
                ops += 1
        return ops

    @staticmethod
    def _check_detection(boards: tuple[Board, ...]) -> int:
        ops = 0
        for board in boards:
            board.is_check()
            ops += 1
        return ops

    @staticmethod
    def _game_simulation(boards: tuple[Board, ...]) -> int:
        """Simulate a 2-ply search: gen moves → make → gen opponent moves → unmake.

        This is the realistic inner loop of an alpha-beta search engine.
        """
        ops = 0
        for board in boards:
            for move in board.generate_legal_moves():
                board.push(move)
                opponent_moves = board.generate_legal_moves()
                ops += len(opponent_moves)
                board.pop()
        return ops


if __name__ == "__main__":
    unittest.main()
