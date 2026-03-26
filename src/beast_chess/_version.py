import tomllib
from pathlib import Path


def get_base_version() -> str:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject_path.open("rb") as pyproject_file:
        pyproject_data = tomllib.load(pyproject_file)

    return pyproject_data["project"]["version"]


def get_source_version() -> str:
    return f"{get_base_version()}-dev"


__version__ = get_source_version()
