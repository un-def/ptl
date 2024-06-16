import pytest

from ptl.exceptions import ExecutableNotFound
from ptl.providers import process_command_line

from .base import BaseTestSuite


class TestSuite(BaseTestSuite):

    def test_absolute_path(self) -> None:
        exec_path = self.tmp_path / 'path' / 'to' / 'exec.sh'
        self.create_executable(exec_path)

        command_line = process_command_line((str(exec_path), 'sync'))

        assert command_line == [str(exec_path), 'sync']

    def test_relative_path(self) -> None:
        exec_path = self.tmp_cwd / 'exec.sh'
        self.create_executable(exec_path)

        command_line = process_command_line('./exec.sh sync')

        assert command_line == [str(exec_path), 'sync']

    def test_exec_name(self) -> None:
        bin_dir = self.override_path_variable()
        exec_path = bin_dir / 'exec.sh'
        self.create_executable(exec_path)

        command_line = process_command_line(['exec.sh', 'sync'])

        assert command_line == [str(exec_path), 'sync']

    def test_not_found_does_not_exist(self) -> None:
        with pytest.raises(ExecutableNotFound, match='does not exist'):
            process_command_line(str(self.tmp_path / 'doesnotexist.sh'))

    def test_not_found_not_a_file(self) -> None:
        with pytest.raises(ExecutableNotFound, match='not a file'):
            process_command_line(str(self.tmp_path))

    def test_not_found_not_in_path(self) -> None:
        self.override_path_variable()
        with pytest.raises(ExecutableNotFound, match='not in PATH'):
            process_command_line('doesnotexist.sh')
