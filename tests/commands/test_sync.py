import subprocess
from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest

from ptl.commands import sync
from ptl.exceptions import SyncError

from tests.testlib import InFileTestSuite


class TestSuite(InFileTestSuite):
    monkeypatch: pytest.MonkeyPatch
    tmp_cwd: Path
    check_call_mock: Mock

    command_line = ['dummy', 'sync']

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch: pytest.MonkeyPatch, tmp_cwd: Path) -> None:
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
        expected_files: List[Path] = []
        for lockfile in ['grandparent.txt', 'parent.txt', 'child.txt']:
            self.create_file(lockfile)
            expected_files.append(Path(lockfile))

        sync(command_line=self.command_line, input_dir=self.input_dir)

        self.check_call_mock.assert_called_once_with(
            self.command_line + expected_files)

    def test_ok_abs_path(self) -> None:
        self.create_file('grandparent.in')
        self.create_file('parent.in', '-r grandparent.txt')
        self.create_file('child.in', '-c parent.txt')
        expected_files: List[Path] = []
        for lockfile in ['grandparent.txt', 'parent.txt', 'child.txt']:
            expected_files.append(self.create_file(lockfile))

        sync(command_line=self.command_line, input_dir=self.input_dir)

        self.check_call_mock.assert_called_once_with(
            self.command_line + expected_files)

    def test_error_missing_compiled_files(self) -> None:
        self.create_file('child.in', '-c parent.txt')
        self.create_file('parent.in', '-r grandparent.txt')
        self.create_file('grandparent.in')
        self.create_file('parent.txt')

        with pytest.raises(
            SyncError, match='missing: grandparent.txt, child.txt',
        ):
            sync(command_line=self.command_line, input_dir=self.input_dir)

    def test_error_from_subprocess(self) -> None:
        self.create_file('deps.in')
        self.create_file('deps.txt')
        self.check_call_mock.side_effect = subprocess.CalledProcessError(
            returncode=5, cmd=self.command_line, output='boom!')

        with pytest.raises(
            SyncError,
            match='dummy sync returned non-zero exit status 5:\nboom!',
        ):
            sync(command_line=self.command_line, input_dir=self.input_dir)
