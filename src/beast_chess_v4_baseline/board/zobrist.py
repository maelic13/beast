from __future__ import annotations

from random import Random

_RNG = Random(0xB3A57C0DE)

PIECE_KEYS = tuple(tuple(_RNG.getrandbits(64) for _ in range(64)) for _ in range(13))
CASTLING_KEYS = tuple(_RNG.getrandbits(64) for _ in range(16))
EN_PASSANT_FILE_KEYS = tuple(_RNG.getrandbits(64) for _ in range(8))
SIDE_TO_MOVE_KEY = _RNG.getrandbits(64)
