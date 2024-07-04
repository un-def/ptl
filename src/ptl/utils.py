from pathlib import Path


def try_relative_to(path: Path, relative_to: Path) -> Path:
    try:
        return path.relative_to(relative_to)
    except ValueError:
        return path


def is_path(name_or_path: str) -> bool:
    if name_or_path == '.' or name_or_path == '..':
        return True
    # name => False
    # /foo/bar/name, bar/name, ./name => True
    return Path(name_or_path).name != name_or_path
