from pathlib import Path
from textwrap import dedent
from typing import Optional

import pytest


class BaseTestSuite:
    input_dir: Path

    @pytest.fixture(autouse=True)
    def base_setup(self, tmp_path: Path) -> None:
        input_dir = tmp_path / 'input_dir'
        input_dir.mkdir()
        self.input_dir = input_dir

    def create_infile(self, name: str, content: Optional[str] = None) -> Path:
        if not name.endswith('.in'):
            name = f'{name}.in'
        infile = self.input_dir / name
        if content:
            infile.write_text(dedent(content.lstrip('\n')))
        else:
            infile.touch()
        return infile
