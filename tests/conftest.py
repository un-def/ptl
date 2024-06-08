import os
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture
def tmp_cwd(tmp_path: Path) -> Iterator[Path]:
    cwd = os.getcwd()
    tmp_cwd = tmp_path / 'tmp_cwd'
    tmp_cwd.mkdir()
    os.chdir(tmp_cwd)
    yield tmp_cwd
    os.chdir(cwd)
