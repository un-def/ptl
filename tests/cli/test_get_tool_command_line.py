from unittest.mock import Mock

import pytest

from ptl.cli import Args, build_parser, get_tool_command_line
from ptl.config import Config
from ptl.providers import (
    Provider, Tool, check_tool_version, find_tool, process_command_line,
)


@pytest.fixture
def config_mock() -> Mock:
    mock = Mock(spec_set=Config)
    mock.get_tool.return_value = None
    return mock


def parse_args(*args: str) -> Args:
    return build_parser().parse_args(args, namespace=Args())


@pytest.mark.parametrize(['command', 'flag', 'expected_command_line'], [
    ('compile', '--pip-tools', 'pip-compile'),
    ('compile', '--uv', 'uv pip compile'),
    ('sync', '--pip-tools', 'pip-sync'),
    ('sync', '--uv', 'uv pip sync'),
])
def test_tool_provider_from_args(
    monkeypatch: pytest.MonkeyPatch, config_mock: Mock,
    command: str, flag: str, expected_command_line: str,
) -> None:
    check_tool_version_mock = Mock(
        spec_set=check_tool_version,
        return_value=(['/path/to/tool', command], f'{command} 0.0.1'),
    )
    monkeypatch.setattr('ptl.cli.check_tool_version', check_tool_version_mock)
    args = parse_args(command, flag)

    command_line = get_tool_command_line(config_mock, args)

    assert command_line == ['/path/to/tool', command]
    config_mock.get_tool.assert_not_called()
    check_tool_version_mock.assert_called_once_with(expected_command_line)


def test_custom_tool_from_args(
    monkeypatch: pytest.MonkeyPatch, config_mock: Mock,
) -> None:
    process_command_line_mock = Mock(
        spec_set=process_command_line,
        return_value=['/path/to/dummy', 'compile'],
    )
    monkeypatch.setattr(
        'ptl.cli.process_command_line', process_command_line_mock)
    args = parse_args('compile', '--tool="dummy compile"')

    command_line = get_tool_command_line(config_mock, args)

    assert command_line == ['/path/to/dummy', 'compile']
    config_mock.get_tool.assert_not_called()
    process_command_line_mock.assert_called_once_with('"dummy compile"')


@pytest.mark.parametrize(['command', 'provider', 'expected_command_line'], [
    ('compile', Provider.PIP_TOOLS, 'pip-compile'),
    ('compile', Provider.UV, 'uv pip compile'),
    ('sync', Provider.PIP_TOOLS, 'pip-sync'),
    ('sync', Provider.UV, 'uv pip sync'),
])
def test_tool_provider_from_config(
    monkeypatch: pytest.MonkeyPatch, config_mock: Mock,
    command: str, provider: Provider, expected_command_line: str,
) -> None:
    config_mock.get_tool.return_value = provider
    check_tool_version_mock = Mock(
        spec_set=check_tool_version,
        return_value=(['/path/to/tool', command], f'{command} 0.0.1'),
    )
    monkeypatch.setattr('ptl.cli.check_tool_version', check_tool_version_mock)
    args = parse_args(command)

    command_line = get_tool_command_line(config_mock, args)

    assert command_line == ['/path/to/tool', command]
    config_mock.get_tool.assert_called_once_with(Tool(command))
    check_tool_version_mock.assert_called_once_with(expected_command_line)


def test_custom_tool_from_config(
    monkeypatch: pytest.MonkeyPatch, config_mock: Mock,
) -> None:
    config_mock.get_tool.return_value = 'dummy sync'
    process_command_line_mock = Mock(
        spec_set=process_command_line,
        return_value=['/path/to/dummy', 'sync'],
    )
    monkeypatch.setattr(
        'ptl.cli.process_command_line', process_command_line_mock)
    args = parse_args('sync')

    command_line = get_tool_command_line(config_mock, args)

    assert command_line == ['/path/to/dummy', 'sync']
    config_mock.get_tool.assert_called_once_with(Tool.SYNC)
    process_command_line_mock.assert_called_once_with('dummy sync')


@pytest.mark.parametrize(['command', 'expected_tool'], [
    ('compile', Tool.COMPILE),
    ('sync', Tool.SYNC),
])
def test_autodiscovery(
    monkeypatch: pytest.MonkeyPatch, config_mock: Mock,
    command: str, expected_tool: Tool,
) -> None:
    find_tool_mock = Mock(
        spec_set=find_tool,
        return_value=(['/path/to/uv', 'pip', command], f'pip {command} 0.0.1'),
    )
    monkeypatch.setattr('ptl.cli.find_tool', find_tool_mock)
    args = parse_args(command)

    command_line = get_tool_command_line(config_mock, args)

    assert command_line == ['/path/to/uv', 'pip', command]
    config_mock.get_tool.assert_called_once_with(expected_tool)
    find_tool_mock.assert_called_once_with(expected_tool)
