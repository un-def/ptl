from pathlib import Path

import pytest

from ptl.exceptions import InputDirectoryError
from ptl.infile import get_input_dir


def test_passed_path_not_a_dir(tmp_path: Path):
    path = tmp_path / 'file'
    path.touch()

    with pytest.raises(
        InputDirectoryError, match=f'{path} is not a directory',
    ):
        get_input_dir(path)


def test_passed_path_does_not_exist(tmp_path: Path):
    path = tmp_path / 'requirements'

    with pytest.raises(InputDirectoryError, match=f'{path} does not exist'):
        get_input_dir(path)


def test_autodiscovery_requirements_dir(tmp_cwd: Path):
    path = tmp_cwd / 'requirements'
    path.mkdir()

    input_dir = get_input_dir()

    assert input_dir == path


def test_autodiscovery_current_dir(tmp_cwd: Path):
    (tmp_cwd / 'base.in').touch()

    input_dir = get_input_dir()

    assert input_dir == tmp_cwd


@pytest.mark.usefixtures('tmp_cwd')
def test_autodiscovery_not_found():
    with pytest.raises(InputDirectoryError, match='input directory not found'):
        get_input_dir()
