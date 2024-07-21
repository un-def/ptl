import logging
from pathlib import Path
from typing import List, Optional, Union
from unittest.mock import Mock

import pytest

from ptl import commands
from ptl.cli import configure_logging, do_main, get_tool_command_line, main
from ptl.config import Config
from ptl.exceptions import InputDirectoryError


@pytest.fixture
def config_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock(spec_set=Config)
    mock.return_value = mock
    monkeypatch.setattr('ptl.cli.Config', mock)
    mock.directory = None
    mock.verbosity = 0
    mock.get_tool.return_value = None
    mock.get_tool_options.return_value = None
    return mock


@pytest.fixture
def get_tool_command_line_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock(
        spec_set=get_tool_command_line,
        return_value=['/path/to/dummy', 'command'],
    )
    monkeypatch.setattr('ptl.cli.get_tool_command_line', mock)
    return mock


@pytest.fixture
def sync_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock(spec_set=commands.sync)
    monkeypatch.setattr(commands, 'sync', mock)
    return mock


@pytest.fixture
def compile_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock(spec_set=commands.compile)
    monkeypatch.setattr(commands, 'compile', mock)
    return mock


@pytest.fixture
def show_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock(spec_set=commands.show)
    monkeypatch.setattr(commands, 'show', mock)
    return mock


def test_error_reporing(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    caplog.set_level(logging.ERROR)
    mock = Mock(
        spec_set=do_main, side_effect=InputDirectoryError('does not exist'))
    monkeypatch.setattr('ptl.cli.do_main', mock)

    with pytest.raises(SystemExit) as excinfo:
        main([])

    assert excinfo.value.code == 1
    assert caplog.messages == ['InputDirectoryError: does not exist']


def test_sys_argv_is_used_if_args_not_passed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr('sys.argv', ['/path/to/script', '--foo', '--bar'])
    mock = Mock(spec_set=do_main)
    monkeypatch.setattr('ptl.cli.do_main', mock)

    main()

    mock.assert_called_once_with(['--foo', '--bar'])


def test_extra_args_not_allowed_if_not_tool(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(['show', '--foo'])

    assert excinfo.value.code != 0
    assert 'unrecognized arguments: --foo' in capsys.readouterr().err


@pytest.mark.parametrize(['flags', 'config_value', 'expected_verbosity'], [
    ([], -100, -100),
    (['--verbose'], -100, 1),
    (['--verbose', '-v'], -100, 2),
    (['-vvv'], -100, 3),
    (['--quiet'], -100, -1),
    (['-q', '--quiet'], -100, -2),
    (['-qqq'], -100, -3),
])
@pytest.mark.usefixtures('get_tool_command_line_mock', 'compile_mock')
def test_configure_logging_call(
    monkeypatch: pytest.MonkeyPatch, config_mock: Mock,
    flags: List[str], config_value: int, expected_verbosity: int,
) -> None:
    config_mock.verbosity = config_value
    mock = Mock(spec_set=configure_logging)
    monkeypatch.setattr('ptl.cli.configure_logging', mock)

    main(['compile'] + flags)

    mock.assert_called_once_with(expected_verbosity)


@pytest.mark.parametrize(['args', 'expected_path', 'expected_no_config'], [
    ([], None, None),
    (['-c', 'custom.toml'], 'custom.toml', None),
    (['--config=/path/to/conf.toml'], '/path/to/conf.toml', None),
    (['--no-config'], None, True),
])
def test_config_call(
    config_mock: Mock, args: List[str],
    expected_path: str, expected_no_config: bool,
) -> None:
    # here we use side_effect to abort main() execution early
    config_mock.side_effect = RuntimeError

    with pytest.raises(RuntimeError):
        main(['sync'] + args)

    config_mock.assert_called_once_with(
        expected_path, ignore_config_file=expected_no_config)


@pytest.mark.parametrize(
    [
        'command_line', 'config_directory', 'config_tool_options',
        'expected_command_line', 'expected_input_dir',
        'expected_layers', 'expected_include_parent_layers',
    ], [
        (
            ['compile'], None, None,
            [], None, None, True,
        ),
        (
            # --only without layers ignored
            ['compile', '-q', '-q', '--only', '--foo'], None, [],
            ['-qq', '--foo'], None, None, True,
        ),
        (
            ['compile', '--only', 'dev', 'main'], Path('reqs'), None,
            [], Path('reqs'), ['dev', 'main'], False,
        ),
        (
            ['compile', '--verbose', '-d', 'reqs', 'dev'], Path('ignored'),
            None,
            ['-v'], 'reqs', ['dev'], True,
        ),
        (
            # tool options from config
            ['compile'], None, ['-x', '--dry-run'],
            ['-x', '--dry-run'], None, None, True,
        ),
        (
            # tool options from extra args, config ignored
            ['compile', '-Y'], None, ['-x', '--dry-run'],
            ['-Y'], None, None, True,
        ),
        (
            # extra args with layers
            ['compile', '--quiet', 'dev', 'main', '-P', 'pytest'], None, None,
            ['-q', '-P', 'pytest'], None, ['dev', 'main'], True,
        ),
        (
            # extra args without layers
            ['compile', '-v', '-v', '-P', 'pytest'], None, None,
            ['-vv', '-P', 'pytest'], None, None, True,
        ),
    ]
)
def test_compile_call(
    config_mock: Mock, get_tool_command_line_mock: Mock, compile_mock: Mock,
    command_line: List[str], config_directory: Optional[Path],
    config_tool_options: Optional[List[str]], expected_command_line: List[str],
    expected_input_dir: Union[Path, str, None],
    expected_layers: Optional[List[str]], expected_include_parent_layers: bool,
) -> None:
    config_mock.directory = config_directory
    config_mock.get_tool_options.return_value = config_tool_options
    _expected_command_line = (
        get_tool_command_line_mock.return_value + expected_command_line)

    main(command_line)

    compile_mock.assert_called_once_with(
        command_line=_expected_command_line,
        input_dir=expected_input_dir,
        layers=expected_layers,
        include_parent_layers=expected_include_parent_layers,
    )


@pytest.mark.parametrize(
    [
        'command_line', 'config_directory', 'config_tool_options',
        'expected_command_line', 'expected_input_dir',
        'expected_layers', 'expected_include_parent_layers',
    ], [
        (
            ['sync'], None, None,
            [], None, None, True,
        ),
        (
            ['sync', '--only', 'dev', 'main'], None, [],
            [], None, ['dev', 'main'], False,
        ),
        (
            ['sync', 'dev'], None, None,
            [], None, ['dev'], True,
        ),
        (
            # --only without layers ignored
            ['sync', '--only'], None, None,
            [], None, None, True,
        ),
        (
            ['sync', '--directory', './req', '--quiet'], Path('ignored'), None,
            ['-q'], './req', None, True,
        ),
        (
            ['sync', '-B', '-v', '--foo', '-vv'], Path('reqs'), None,
            ['-B', '-v', '--foo', '-vv'], Path('reqs'), None, True,
        ),
        (
            # tool options from config
            ['sync', 'dev'], None, ['-x', '--dry-run'],
            ['-x', '--dry-run'], None, ['dev'], True,
        ),
        (
            # tool options from extra args, config ignored
            ['sync', 'dev', '-Y'], None, ['-x', '--dry-run'],
            ['-Y'], None, ['dev'], True,
        ),
        (
            # extra args with layers
            ['sync', 'dev', 'main', '-P', 'pytest'], None, None,
            ['-P', 'pytest'], None, ['dev', 'main'], True,
        ),
        (
            # extra args without layers
            ['sync', '-P', 'pytest'], None, None,
            ['-P', 'pytest'], None, None, True,
        ),
    ]
)
def test_sync_call(
    config_mock: Mock, get_tool_command_line_mock: Mock, sync_mock: Mock,
    command_line: List[str], config_directory: Optional[Path],
    config_tool_options: Optional[List[str]],
    expected_command_line: List[str],
    expected_input_dir: Union[Path, str, None],
    expected_layers: Optional[List[str]], expected_include_parent_layers: bool,
) -> None:
    config_mock.directory = config_directory
    config_mock.get_tool_options.return_value = config_tool_options
    _expected_command_line = (
        get_tool_command_line_mock.return_value + expected_command_line)

    main(command_line)

    sync_mock.assert_called_once_with(
        command_line=_expected_command_line,
        input_dir=expected_input_dir,
        layers=expected_layers,
        include_parent_layers=expected_include_parent_layers,
    )


@pytest.mark.parametrize(
    [
        'command_line', 'config_directory', 'expected_input_dir',
        'expected_layers', 'expected_include_parent_layers',
    ], [
        (
            ['show', '--verbose'], None,
            None, None, True,
        ),
        (
            ['show', '-c', 'conf.toml'], Path('path/to/reqs'),
            Path('path/to/reqs'), None, True,
        ),
        (
            ['show', '-q', '--directory', './req', '-q'], Path('ignored'),
            './req', None, True,
        ),
        (
            ['show', '--only', 'dev', 'main'], None,
            None, ['dev', 'main'], False,
        ),
        (
            ['show', 'dev'], None,
            None, ['dev'], True,
        ),
    ]
)
def test_show_call(
    config_mock: Mock, show_mock: Mock, command_line: List[str],
    config_directory: Optional[Path],
    expected_input_dir: Union[Path, str, None],
    expected_layers: Optional[List[str]], expected_include_parent_layers: bool,
) -> None:
    config_mock.directory = config_directory

    main(command_line)

    show_mock.assert_called_once_with(
        input_dir=expected_input_dir,
        layers=expected_layers,
        include_parent_layers=expected_include_parent_layers,
    )
