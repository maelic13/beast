from collections.abc import Callable

import chess
import numpy as np

from .net_input_v1 import board_to_input as net_input_v1
from .net_input_v2 import board_to_input as net_input_v2
from .net_input_version import NetInputVersion

NET_MAP: dict[NetInputVersion, Callable[[chess.Board], np.ndarray]] = {
    NetInputVersion.V1: net_input_v1,
    NetInputVersion.V2: net_input_v2,
}


class NetInputFactory:
    @classmethod
    def from_string(cls, version_string: str) -> Callable[[chess.Board], np.ndarray]:
        return cls.from_version(NetInputVersion.from_string(version_string))

    @classmethod
    def from_version(cls, version: NetInputVersion) -> Callable[[chess.Board], np.ndarray]:
        return NET_MAP.get(version)
