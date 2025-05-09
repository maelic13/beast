from .net import Net
from .net_v1 import NetV1
from .net_v2 import NetV2
from .net_version import NetVersion


class NetFactory:
    NET_MAP: dict[NetVersion, Net] = {
        NetVersion.V1: NetV1(),
        NetVersion.V2: NetV2(),
    }

    @classmethod
    def from_string(cls, version_string: str) -> Net:
        return cls.from_version(NetVersion.from_string(version_string))

    @classmethod
    def from_version(cls, version: NetVersion) -> Net:
        return cls.NET_MAP.get(version)
