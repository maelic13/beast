from pathlib import Path


class Constants:
    ROOT_PATH = Path(__file__).parent.parent.parent
    DATA_PATH = ROOT_PATH / "data"
    MODELS_PATH = ROOT_PATH / "models"
