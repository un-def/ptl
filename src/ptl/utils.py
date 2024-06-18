from pathlib import Path


def try_relative_to(path: Path, relative_to: Path) -> Path:
    try:
        return path.relative_to(relative_to)
    except ValueError:
        return path
