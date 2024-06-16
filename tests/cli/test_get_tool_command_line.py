from unittest.mock import Mock

import pytest

from ptl.cli import Args, build_parser, get_tool_command_line
from ptl.providers import (
    Tool, check_tool_version, find_tool, process_command_line,
)


def parse_args(*args: str) -> Args:
    return build_parser().parse_args(args, namespace=Args())


@pytest.mark.parametrize(['command', 'flag', 'expected_command_line'], [
    ('compile', '--pip-tools', 'pip-compile'),
    ('compile', '--uv', 'uv pip compile'),
    ('sync', '--pip-tools', 'pip-sync'),
    ('sync', '--uv', 'uv pip sync'),
])
def test_tool_flag(
    monkeypatch: pytest.MonkeyPatch, command: str, flag: str,
    expected_command_line: str,
):
    mock = Mock(
        spec_set=check_tool_version,
        return_value=(['/path/to/tool', command], f'{command} 0.0.1'),
    )
    monkeypatch.setattr('ptl.cli.check_tool_version', mock)
    args = parse_args(command, flag)

    command_line = get_tool_command_line(args)

    assert command_line == ['/path/to/tool', command]
    mock.assert_called_once_with(expected_command_line)


def test_custom_tool(monkeypatch: pytest.MonkeyPatch):
    mock = Mock(
        spec_set=process_command_line,
        return_value=['/path/to/dummy', 'compile'],
    )
    monkeypatch.setattr('ptl.cli.process_command_line', mock)
    args = parse_args('compile', '--tool="dummy compile"')

    command_line = get_tool_command_line(args)

    assert command_line == ['/path/to/dummy', 'compile']
    mock.assert_called_once_with('"dummy compile"')


@pytest.mark.parametrize(['command', 'expected_tool'], [
    ('compile', Tool.COMPILE),
    ('sync', Tool.SYNC),
])
def test_autodiscovery(
    monkeypatch: pytest.MonkeyPatch, command: str, expected_tool: Tool,
):
    mock = Mock(
        spec_set=find_tool,
        return_value=(['/path/to/uv', 'pip', command], f'pip {command} 0.0.1'),
    )
    monkeypatch.setattr('ptl.cli.find_tool', mock)
    args = parse_args(command)

    command_line = get_tool_command_line(args)

    assert command_line == ['/path/to/uv', 'pip', command]
    mock.assert_called_once_with(expected_tool)
