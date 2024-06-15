import pytest

from ptl.exceptions import ExecutableNotFound
from ptl.providers import find_executable

from .base import BaseTestSuite


class TestSuite(BaseTestSuite):

    def test_absolute_path(self):
        exec_path = self.tmp_path / 'path' / 'to' / 'exec.sh'
        self.create_executable(exec_path)

        path = find_executable(exec_path)

        assert path == exec_path

    @pytest.mark.parametrize('rel_path', ['./exec.sh', 'dir/exec.sh'])
    def test_relative_path(self, rel_path: str):
        exec_path = self.tmp_cwd / rel_path
        self.create_executable(exec_path)

        path = find_executable(rel_path)

        assert path == exec_path

    def test_exec_name(self):
        bin_dir = self.override_path_variable()
        exec_path = bin_dir / 'exec.sh'
        self.create_executable(exec_path)

        path = find_executable('exec.sh')

        assert path == exec_path

    def test_not_found_does_not_exist(self):
        with pytest.raises(ExecutableNotFound, match='does not exist'):
            find_executable(self.tmp_path / 'doesnotexist.sh')

    def test_not_found_not_a_file(self):
        with pytest.raises(ExecutableNotFound, match='not a file'):
            find_executable(self.tmp_path)

    def test_not_found_not_in_path(self):
        self.override_path_variable()
        with pytest.raises(ExecutableNotFound, match='not in PATH'):
            find_executable('doesnotexist.sh')
