from pathlib import Path
import tomllib

from ._version import __version__ as _build_version


def _get_source_version() -> str | None:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    with pyproject_path.open("rb") as pyproject_file:
        pyproject_data = tomllib.load(pyproject_file)

    version = pyproject_data.get("project", {}).get("version")
    if version is None:
        return None

    return f"{version}-dev"


__version__ = _get_source_version() or _build_version
