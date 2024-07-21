from pathlib import Path

import pytest

from ptl.config import load_config
from ptl.exceptions import ConfigError

from tests.testlib import dedent


def _write_config(path: Path, content: str) -> Path:
    path.write_text(dedent(content))
    return path


def test_error_does_not_exist(tmp_path: Path) -> None:
    config_path = tmp_path / 'conf.toml'

    with pytest.raises(ConfigError, match=r'conf\.toml does not exist'):
        load_config(config_path)


def test_error_not_a_file(tmp_path: Path) -> None:
    config_path = tmp_path / 'conf.toml'
    config_path.mkdir()

    with pytest.raises(ConfigError, match=r'conf\.toml is not a file'):
        load_config(config_path)


def test_error_toml_decode_error(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path / 'conf.toml', """
        [tool.ptl
        directory = "path/to/reqs"
    """)

    with pytest.raises(ConfigError, match=r"conf\.toml: Expected ']'"):
        load_config(config_path)


def test_error_tool_is_not_a_table(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path / 'conf.toml', """
        tool = 100
    """)

    with pytest.raises(ConfigError, match=r'tool must be a table, got int'):
        load_config(config_path)


def test_error_tool_ptl_is_not_a_table(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path / 'conf.toml', """
        [tool]
        ptl = "notatable"
    """)

    with pytest.raises(
        ConfigError, match=r'tool\.ptl must be a table, got str',
    ):
        load_config(config_path)


def test_error_no_toml_parser(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr('ptl.config.toml_load', None)
    config_path = _write_config(tmp_path / 'config.toml', """
        [tool.ptl]
        directory = "path/to/reqs"
    """)

    with pytest.raises(ConfigError, match='no toml parser found'):
        load_config(config_path)


def test_ok_no_ptl_table(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path / 'config.toml', """
        [tool.foobar]
        directory = "path/to/reqs"
    """)

    config_dict = load_config(config_path)

    assert config_dict is None


def test_ok_with_ptl_table(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path / 'config.toml', """
        [tool.ptl]
        tool = ":pip-tools:"

        [tool.ptl.compile]
        tool-options = "--upgrade --no-annotate"

        [tool.ptl.sync]
        tool-options = "--ask"
    """)

    config_dict = load_config(config_path)

    assert config_dict == {
        'tool': ':pip-tools:',
        'compile': {
            'tool-options': '--upgrade --no-annotate',
        },
        'sync': {
            'tool-options': '--ask',
        },
    }
