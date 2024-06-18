from pathlib import Path

from ptl.utils import try_relative_to


def test_ok(tmp_path: Path) -> None:
    path = tmp_path / 'dir' / 'file'

    rel_path = try_relative_to(path, tmp_path)

    assert rel_path == Path('dir/file')


def test_not_subpath(tmp_path: Path) -> None:
    path = tmp_path / 'dir' / 'file'

    abs_path = try_relative_to(path, tmp_path / 'otherdir')

    assert abs_path == path
