import textwrap
from pathlib import Path
from typing import Optional

import pytest


def dedent(text: str, *, strip: bool = True) -> str:
    if strip:
        text = text.lstrip('\n')
    return textwrap.dedent(text)


class InFileTestSuite:
    input_dir: Path

    @pytest.fixture(autouse=True)
    def base_setup(self, input_dir: Path) -> None:
        self.input_dir = input_dir

    dedent = staticmethod(dedent)

    def create_infile(self, name: str, content: Optional[str] = None) -> Path:
        infile = self.input_dir / name
        if content:
            infile.write_text(self.dedent(content))
        else:
            infile.touch()
        return infile
