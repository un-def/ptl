from pathlib import Path

import pytest


pytest.register_assert_rewrite('tests.testlib')


@pytest.fixture
def tmp_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    tmp_cwd = tmp_path / 'tmp_cwd'
    tmp_cwd.mkdir()
    monkeypatch.chdir(tmp_cwd)
    return tmp_cwd


@pytest.fixture
def input_dir(tmp_path: Path) -> Path:
    input_dir = tmp_path / 'input_dir'
    input_dir.mkdir()
    return input_dir
