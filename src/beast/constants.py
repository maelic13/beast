from pathlib import Path


class Constants:
    # engine info
    AUTHOR = "Miloslav Macurek"
    ENGINE_NAME = "Beast"
    ENGINE_VERSION = "2.1"

    # constants
    BEST_MODEL = "v2-2.onnx"
    DEFAULT_DEPTH: float = 2
    INFINITE_DEPTH = float("inf")
    TIME_FLEX = 10  # [ms]

    # paths
    ROOT_PATH = Path(__file__).parent.parent.parent
    DATA_PATH = ROOT_PATH / "data"
    NETS_PATH = ROOT_PATH / "models"
