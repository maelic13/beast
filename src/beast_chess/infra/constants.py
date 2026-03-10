from beast_chess import __version__


class Constants:
    # engine info
    AUTHOR = "Miloslav Macurek"
    ENGINE_NAME = "Beast"
    ENGINE_VERSION = __version__

    # constants
    DEFAULT_DEPTH: int = 2
    INFINITE_DEPTH: int = 10000
    TIME_FLEX = 100  # [ms]
