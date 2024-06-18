import subprocess
from pathlib import Path
from unittest.mock import Mock, call

import pytest

from ptl.commands import compile
from ptl.exceptions import CompileError

from tests.testlib import InFileTestSuite


class TestSuite(InFileTestSuite):
    monkeypatch: pytest.MonkeyPatch
    tmp_cwd: Path
    check_call_mock: Mock

    command_line = ['dummy', 'compile']

    @pytest.fixture(autouse=True)
    def setup(
        self, base_setup: None, monkeypatch: pytest.MonkeyPatch, tmp_cwd: Path,
    ) -> None:
        self.monkeypatch = monkeypatch
        self.tmp_cwd = tmp_cwd
        check_call_mock = Mock(spec_set=subprocess.check_call)
        monkeypatch.setattr(subprocess, 'check_call', check_call_mock)
        self.check_call_mock = check_call_mock

    def test_ok_rel_path(self) -> None:
        self.monkeypatch.chdir(self.input_dir)
        self.create_file('grandparent.in')
        self.create_file('parent.in', '-r grandparent.txt')
        self.create_file('child.in', '-c parent.txt')

        compile(command_line=self.command_line, input_dir=self.input_dir)

        assert self.check_call_mock.call_count == 3
        self.check_call_mock.assert_has_calls([
            call(self.command_line + [
                Path('grandparent.ptl.in'), '-o', Path('grandparent.txt')]),
            call(self.command_line + [
                Path('parent.ptl.in'), '-o', Path('parent.txt')]),
            call(self.command_line + [
                Path('child.ptl.in'), '-o', Path('child.txt')]),
        ])

    def test_ok_abs_path(self) -> None:
        self.create_file('grandparent.in')
        self.create_file('parent.in', '-r grandparent.txt')
        self.create_file('child.in', '-c parent.txt')
        dir_ = self.input_dir

        compile(command_line=self.command_line, input_dir=self.input_dir)

        assert self.check_call_mock.call_count == 3
        self.check_call_mock.assert_has_calls([
            call(self.command_line + [
                dir_ / 'grandparent.ptl.in', '-o', dir_ / 'grandparent.txt']),
            call(self.command_line + [
                dir_ / 'parent.ptl.in', '-o', dir_ / 'parent.txt']),
            call(self.command_line + [
                dir_ / 'child.ptl.in', '-o', dir_ / 'child.txt']),
        ])

    def test_error_from_subprocess(self) -> None:
        self.create_file('deps.in')
        self.check_call_mock.side_effect = subprocess.CalledProcessError(
            returncode=5, cmd=self.command_line, output='boom!')

        with pytest.raises(
            CompileError,
            match='dummy compile returned non-zero exit status 5:\nboom!',
        ):
            compile(command_line=self.command_line, input_dir=self.input_dir)
