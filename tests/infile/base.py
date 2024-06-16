from pathlib import Path
from textwrap import dedent
from typing import Optional

import pytest


class BaseTestSuite:
    input_dir: Path

    @pytest.fixture(autouse=True)
    def base_setup(self, input_dir: Path) -> None:
        self.input_dir = input_dir

    def create_infile(self, name: str, content: Optional[str] = None) -> Path:
        infile = self.input_dir / name
        if content:
            infile.write_text(dedent(content.lstrip('\n')))
        else:
            infile.touch()
        return infile
