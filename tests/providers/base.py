from pathlib import Path

import pytest

from tests.testlib import dedent


class BaseTestSuite:
    monkeypatch: pytest.MonkeyPatch
    tmp_path: Path
    tmp_cwd: Path

    exec_sh = dedent("""
        #!/bin/sh
        if [ $# -lt 1 ]; then
            echo "usage: dummy COMMAND" >&2
            exit 1
        fi
        case "$1" in
            compile|sync)
                ;;
            *)
                echo "unknown tool $1"
                exit 2
        esac
        if [ "$2" = '--version' ]; then
            echo "dummy $1 version 0.0.1"
        else
            echo "I'm a dummy"
            exit 3
        fi
    """)

    @pytest.fixture(autouse=True)
    def base_setup(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, tmp_cwd: Path,
    ) -> None:
        self.monkeypatch = monkeypatch
        self.tmp_path = tmp_path
        self.tmp_cwd = tmp_cwd

    def create_executable(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(mode=0o777, exist_ok=True)
        path.write_text(self.exec_sh)

    def override_path_variable(self) -> Path:
        bin_dir = self.tmp_path / 'bin'
        bin_dir.mkdir(exist_ok=True)
        self.monkeypatch.setenv('PATH', str(bin_dir))
        return bin_dir
