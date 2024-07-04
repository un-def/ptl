import pytest

from ptl.utils import is_path


@pytest.mark.parametrize('value', [
    './name', 'dir/name', '/path/to/name', '.', '..'])
def test_is_path(value: str) -> None:
    assert is_path(value) is True


@pytest.mark.parametrize('value', ['name', '...'])
def test_is_not_path(value: str) -> None:
    assert is_path(value) is False
