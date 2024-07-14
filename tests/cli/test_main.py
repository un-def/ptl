import logging
from typing import List, Optional
from unittest.mock import Mock

import pytest

from ptl import commands
from ptl.cli import configure_logging, do_main, get_tool_command_line, main
from ptl.exceptions import InputDirectoryError


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


@pytest.mark.parametrize(['flags', 'expected_verbosity'], [
    ([], 0),
    (['--verbose'], 1),
    (['--verbose', '-v'], 2),
    (['-vvv'], 3),
    (['--quiet'], -1),
    (['-q', '--quiet'], -2),
    (['-qqq'], -3),
])
@pytest.mark.usefixtures('get_tool_command_line_mock', 'compile_mock')
def test_configure_logging_call(
    monkeypatch: pytest.MonkeyPatch, flags: List[str], expected_verbosity: int,
) -> None:
    mock = Mock(spec_set=configure_logging)
    monkeypatch.setattr('ptl.cli.configure_logging', mock)

    main(['compile'] + flags)

    mock.assert_called_once_with(expected_verbosity)


@pytest.mark.parametrize(
    [
        'command_line', 'expected_command_line', 'expected_input_dir',
        'expected_layers', 'expected_include_parent_layers',
    ], [
        (
            ['compile'],
            [], None, None, True,
        ),
        (
            # --only without layers ignored
            ['compile', '-q', '-q', '--only', '--foo'],
            ['-qq', '--foo'], None, None, True,
        ),
        (
            ['compile', '--only', 'dev', 'main'],
            [], None, ['dev', 'main'], False,
        ),
        (
            ['compile', '--verbose', '-d', 'reqs', 'dev'],
            ['-v'], 'reqs', ['dev'], True,
        ),
        (
            # extra args with layers
            ['compile', '--quiet', 'dev', 'main', '-P', 'pytest'],
            ['-q', '-P', 'pytest'], None, ['dev', 'main'], True,
        ),
        (
            # extra args without layers
            ['compile', '-v', '-v', '-P', 'pytest'],
            ['-vv', '-P', 'pytest'], None, None, True,
        ),
    ]
)
def test_compile_call(
    get_tool_command_line_mock: Mock, compile_mock: Mock,
    command_line: List[str], expected_command_line: List[str],
    expected_input_dir: Optional[str],
    expected_layers: Optional[List[str]], expected_include_parent_layers: bool,
) -> None:
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
        'command_line', 'expected_command_line', 'expected_input_dir',
        'expected_layers', 'expected_include_parent_layers',
    ], [
        (
            ['sync'],
            [], None, None, True,
        ),
        (
            ['sync', '--only', 'dev', 'main'],
            [], None, ['dev', 'main'], False,
        ),
        (
            ['sync', 'dev'],
            [], None, ['dev'], True,
        ),
        (
            # --only without layers ignored
            ['sync', '--only'],
            [], None, None, True,
        ),
        (
            ['sync', '--directory', './req', '--quiet'],
            ['-q'], './req', None, True,
        ),
        (
            ['sync', '-B', '-v', '--foo', '-vv'],
            ['-B', '-v', '--foo', '-vv'], None, None, True,
        ),
        (
            # extra args with layers
            ['sync', 'dev', 'main', '-P', 'pytest'],
            ['-P', 'pytest'], None, ['dev', 'main'], True,
        ),
        (
            # extra args without layers
            ['sync', '-P', 'pytest'],
            ['-P', 'pytest'], None, None, True,
        ),
    ]
)
def test_sync_call(
    get_tool_command_line_mock: Mock, sync_mock: Mock, command_line: List[str],
    expected_command_line: List[str], expected_input_dir: Optional[str],
    expected_layers: Optional[List[str]], expected_include_parent_layers: bool,
) -> None:
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
        'command_line', 'expected_input_dir',
        'expected_layers', 'expected_include_parent_layers',
    ], [
        (
            ['show', '--verbose'],
            None, None, True,
        ),
        (
            ['show', '-q', '--directory', './req', '-q', '--only'],
            './req', None, True,
        ),
        (
            ['show', '--only', 'dev', 'main'],
            None, ['dev', 'main'], False,
        ),
        (
            ['show', 'dev'],
            None, ['dev'], True,
        ),
    ]
)
def test_show_call(
    show_mock: Mock, command_line: List[str],
    expected_input_dir: Optional[str], expected_layers: Optional[List[str]],
    expected_include_parent_layers: bool,
) -> None:
    main(command_line)

    show_mock.assert_called_once_with(
        input_dir=expected_input_dir,
        layers=expected_layers,
        include_parent_layers=expected_include_parent_layers,
    )
