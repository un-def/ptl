import pytest

from ptl.exceptions import ToolVersionCheckFailed
from ptl.providers import check_tool_version

from .base import TestSuiteBase


class TestSuite(TestSuiteBase):

    def test_absolute_path(self) -> None:
        exec_path = self.tmp_path / 'path' / 'to' / 'exec.sh'
        self.create_executable(exec_path)

        command_line, version = check_tool_version((str(exec_path), 'sync'))

        assert command_line == [str(exec_path), 'sync']
        assert version == 'dummy sync version 0.0.1'

    def test_relative_path(self) -> None:
        exec_path = self.tmp_cwd / 'exec.sh'
        self.create_executable(exec_path)

        command_line, version = check_tool_version('./exec.sh compile')

        assert command_line == [str(exec_path), 'compile']
        assert version == 'dummy compile version 0.0.1'

    def test_exec_name(self) -> None:
        bin_dir = self.override_path_variable()
        exec_path = bin_dir / 'exec.sh'
        self.create_executable(exec_path)

        command_line, version = check_tool_version(['exec.sh', 'sync'])

        assert command_line == [str(exec_path), 'sync']
        assert version == 'dummy sync version 0.0.1'

    def test_not_found_does_not_exist(self) -> None:
        with pytest.raises(ToolVersionCheckFailed, match='does not exist'):
            check_tool_version(str(self.tmp_path / 'doesnotexist.sh'))

    def test_not_found_not_a_file(self) -> None:
        with pytest.raises(ToolVersionCheckFailed, match='not a file'):
            check_tool_version(str(self.tmp_path))

    def test_not_found_not_in_path(self) -> None:
        self.override_path_variable()
        with pytest.raises(ToolVersionCheckFailed, match='not in PATH'):
            check_tool_version('doesnotexist.sh')

    def test_check_failed_exit_status_not_ok(self) -> None:
        exec_path = self.tmp_cwd / 'exec.sh'
        self.create_executable(exec_path)

        with pytest.raises(
            ToolVersionCheckFailed,
            match='non-zero exit status.*\nunknown tool foobar',
        ):
            check_tool_version('./exec.sh foobar')
