from pathlib import Path
from typing import List

import pytest

from ptl.config import find_config


@pytest.mark.parametrize(['configs', 'expected'], [
    (['.ptl.toml', 'ptl.toml', 'pyproject.toml'], '.ptl.toml'),
    (['ptl.toml', 'pyproject.toml'], 'ptl.toml'),
    (['pyproject.toml'], 'pyproject.toml'),
])
def test_priority(tmp_cwd: Path, configs: List[str], expected: str) -> None:
    for config in configs:
        (tmp_cwd / config).touch()

    config_path = find_config()

    assert config_path == tmp_cwd / expected


def test_no_config(tmp_cwd: Path) -> None:
    # should be silently ignored
    (tmp_cwd / 'pyproject.toml').mkdir()

    config_path = find_config()

    assert config_path is None
