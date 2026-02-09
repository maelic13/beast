"""Project-wide constants.

All score values are in **centipawns (cp)**.

This file is intentionally dependency-free and safe to import from anywhere.

Why add INFINITE and MATE_SCORE?
--------------------------------
The upgraded search implementation uses:
- `Constants.INFINITE` for alpha-beta window bounds.
- `Constants.MATE_SCORE` for mate-score normalization when storing in the
  transposition table (ply-adjusted mate scores).

These names are common in chess engines and prevent hard-coded magic numbers.
"""


class Constants:
    # Engine info
    AUTHOR: str = "Miloslav Macurek"
    ENGINE_NAME: str = "Beast"
    ENGINE_VERSION: str = "3.2.3"

    # Search / UCI defaults
    DEFAULT_DEPTH: int = 2
    INFINITE_DEPTH: int = 10000

    # Time management
    TIME_FLEX: int = 100  # [ms]

    # --- Scoring constants (centipawns) ---

    # Base mate score. Engine components typically return mate as:
    #   + (MATE_SCORE - ply) for a mate found for side to move
    #   - (MATE_SCORE - ply) for being mated
    # so mates closer in ply are preferred.
    #
    # 32000 is a widely used safe default and comfortably above any reasonable
    # evaluation (material+positional) that stays within a few thousand cp.
    MATE_SCORE: int = 32000

    # Alpha-beta "infinity". Must be >= MATE_SCORE.
    INFINITE: int = 1_000_000

    # Conventional draw score.
    DRAW_SCORE: int = 0

    # (Optional) convenience aliases for compatibility with older code styles.
    INF: int = INFINITE
    MATE: int = MATE_SCORE
