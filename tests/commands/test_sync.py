import subprocess
from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest

from ptl.commands import sync
from ptl.exceptions import LayerFileError, SyncError

from tests.testlib import InFileTestSuite


class TestSuite(InFileTestSuite):
    monkeypatch: pytest.MonkeyPatch
    tmp_cwd: Path
    check_call_mock: Mock

    command_line = ['dummy', 'sync']

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

    def test_ok_specified_layers_with_parents(self) -> None:
        self.create_file('grandparent.in')
        self.create_file('parent.in', '-r grandparent.txt')
        self.create_file('child.in', '-r parent.txt')
        expected_files: List[Path] = []
        for lockfile in ['grandparent.txt', 'parent.txt', 'child.txt']:
            expected_files.append(self.create_file(lockfile))

        sync(
            command_line=self.command_line, input_dir=self.input_dir,
            layers=['child'],
        )

        self.check_call_mock.assert_called_once_with(
            self.command_line + expected_files)

    @pytest.mark.parametrize('create_not_required_lock', [False, True])
    def test_ok_specified_layers_only(
        self, create_not_required_lock: bool,
    ) -> None:
        self.create_file('grandparent.in')
        self.create_file('parent.in', '-r grandparent.txt')
        self.create_file('child.in', '-r parent.txt')
        expected_files: List[Path] = []
        # since child has no direct reference to grandparent, sort_infiles()
        # will put then on the same level and sort lexicographically
        for lockfile in ['child.txt', 'grandparent.txt']:
            expected_files.append(self.create_file(lockfile))
        # presence or absence of this lock file should not affect at all
        if create_not_required_lock:
            self.create_file('parent.txt')

        sync(
            command_line=self.command_line, input_dir=self.input_dir,
            layers=['grandparent.txt', 'child'], include_parent_layers=False,
        )

        self.check_call_mock.assert_called_once_with(
            self.command_line + expected_files)

    @pytest.mark.parametrize(
        'missing_layer', ['layer3', 'layer3.in', 'layer3.txt'])
    def test_error_unknown_layer(self, missing_layer: str) -> None:
        self.create_file('layer1.in')
        self.create_file('layer2.in')

        with pytest.raises(LayerFileError, match='layer3 does not exist'):
            sync(
                command_line=self.command_line,
                input_dir=self.input_dir,
                layers=['layer1', 'layer2', missing_layer],
            )

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
