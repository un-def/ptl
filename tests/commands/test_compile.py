import subprocess
from pathlib import Path
from typing import Union
from unittest.mock import Mock
from unittest.mock import (
    _Call as MockCall,  # pyright: ignore[reportPrivateUsage]
)
from unittest.mock import call

import pytest

from ptl.commands import compile
from ptl.exceptions import CompileError

from tests.testlib import InFileTestSuiteBase


class TestSuite(InFileTestSuiteBase):
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

    def call(self, *args: Union[str, Path]) -> MockCall:
        return call([*self.command_line, *args])

    def test_ok_rel_path(self) -> None:
        self.monkeypatch.chdir(self.input_dir)
        self.create_file('grand.in')
        self.create_file('parent.in', '-r grand.txt')
        self.create_file('child.in', '-c parent.txt')

        compile(command_line=self.command_line, input_dir=self.input_dir)

        assert self.check_call_mock.call_count == 3
        self.check_call_mock.assert_has_calls([
            self.call(Path('grand.ptl.in'), '-o', Path('grand.txt')),
            self.call(Path('parent.ptl.in'), '-o', Path('parent.txt')),
            self.call(Path('child.ptl.in'), '-o', Path('child.txt')),
        ])

    def test_ok_abs_path(self) -> None:
        self.create_file('grand.in')
        self.create_file('parent.in', '-r grand.txt')
        self.create_file('child.in', '-c parent.txt')
        dir_ = self.input_dir

        compile(command_line=self.command_line, input_dir=self.input_dir)

        assert self.check_call_mock.call_count == 3
        self.check_call_mock.assert_has_calls([
            self.call(dir_ / 'grand.ptl.in', '-o', dir_ / 'grand.txt'),
            self.call(dir_ / 'parent.ptl.in', '-o', dir_ / 'parent.txt'),
            self.call(dir_ / 'child.ptl.in', '-o', dir_ / 'child.txt'),
        ])

    def test_ok_specified_layers_with_parents(self) -> None:
        self.monkeypatch.chdir(self.input_dir)
        self.create_file('not-referenced.in')
        self.create_file('grand.in')
        self.create_file('parent.in', '-c grand.txt')
        self.create_file('child.in', '-r parent.txt')

        compile(
            command_line=self.command_line, input_dir=self.input_dir,
            layers=['child'],
        )

        assert self.check_call_mock.call_count == 3
        self.check_call_mock.assert_has_calls([
            self.call(Path('grand.ptl.in'), '-o', Path('grand.txt')),
            self.call(Path('parent.ptl.in'), '-o', Path('parent.txt')),
            self.call(Path('child.ptl.in'), '-o', Path('child.txt')),
        ])

    def test_ok_specified_layers_only(self) -> None:
        self.monkeypatch.chdir(self.input_dir)
        self.create_file('grand.in')
        self.create_file('parent.in', '-c grand')
        self.create_file('parent.txt')
        self.create_file('child.in', '-r parent.txt')

        compile(
            command_line=self.command_line, input_dir=self.input_dir,
            layers=['grand', 'child'], include_parent_layers=False,
        )

        assert self.check_call_mock.call_count == 2
        self.check_call_mock.assert_has_calls([
            self.call(Path('child.ptl.in'), '-o', Path('child.txt')),
            self.call(Path('grand.ptl.in'), '-o', Path('grand.txt')),
        ])

    def test_error_not_compiled(self) -> None:
        self.monkeypatch.chdir(self.input_dir)
        self.create_file('grand.in')
        self.create_file('parent.in', '-c grand')
        self.create_file('child.in', '-r parent')

        with pytest.raises(
            CompileError, match=r'missing: parent\.txt, grand\.txt$',
        ):
            compile(
                command_line=self.command_line, input_dir=self.input_dir,
                layers=['child'], include_parent_layers=False,
            )

    def test_error_from_subprocess(self) -> None:
        self.create_file('deps.in')
        self.check_call_mock.side_effect = subprocess.CalledProcessError(
            returncode=5, cmd=self.command_line, output='boom!')

        with pytest.raises(
            CompileError,
            match='dummy compile returned non-zero exit status 5:\nboom!',
        ):
            compile(command_line=self.command_line, input_dir=self.input_dir)
