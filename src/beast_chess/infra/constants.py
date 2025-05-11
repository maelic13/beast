from importlib.metadata import PackageNotFoundError, version

from beast_chess import __version__ as _dev_version


class Constants:
    # engine info
    AUTHOR = "Miloslav Macurek"
    ENGINE_NAME = "Beast"
    try:
        ENGINE_VERSION = version("beast-chess")
    except PackageNotFoundError:
        ENGINE_VERSION = _dev_version

    # constants
    DEFAULT_DEPTH: float = 2
    INFINITE_DEPTH = float("inf")
    TIME_FLEX = 10  # [ms]
