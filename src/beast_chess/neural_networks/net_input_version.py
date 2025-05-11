from enum import Enum, auto


class NetInputVersion(Enum):
    V1 = auto()
    V2 = auto()

    @classmethod
    def from_string(cls, version_string: str) -> "NetInputVersion":
        if version_string.lower() == cls.V1.name.lower():
            return NetInputVersion.V1

        if version_string.lower() == cls.V2.name.lower():
            return NetInputVersion.V2

        msg = "Invalid version string identifier!"
        raise RuntimeError(msg)
