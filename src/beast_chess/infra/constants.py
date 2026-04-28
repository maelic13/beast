import sys
from pathlib import Path


class Constants:
    # engine info
    AUTHOR = "Miloslav Macurek"
    ENGINE_NAME = "Beast"
    ENGINE_VERSION = "3.3.2"
    DEFAULT_MODEL_FILE = "v1_model2.onnx"

    # constants
    DEFAULT_DEPTH: int = 2
    INFINITE_DEPTH: int = 10000
    TIME_FLEX = 100  # [ms]

    @classmethod
    def default_model_path(cls) -> Path:
        return Path(cls.DEFAULT_MODEL_FILE)

    @staticmethod
    def engine_directory() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[3]

    @classmethod
    def resolve_model_path(cls, model_file: Path) -> Path | None:
        if model_file.is_absolute():
            return model_file if model_file.exists() else None

        if model_file.exists():
            return model_file.resolve()

        engine_relative_path = cls.engine_directory() / model_file
        if engine_relative_path.exists():
            return engine_relative_path.resolve()

        return None
