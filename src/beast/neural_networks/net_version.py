from enum import Enum


class NetVersion(Enum):
    V1 = "v1"
    V2 = "v2"

    @staticmethod
    def from_string(version_string: str) -> "NetVersion":
        if version_string == "v1":
            return NetVersion.V1

        if version_string == "v2":
            return NetVersion.V2

        msg = "Invalid version string identifier!"
        raise RuntimeError(msg)
