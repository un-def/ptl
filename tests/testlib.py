import textwrap
from pathlib import Path
from typing import Optional, Union

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

    def create_file(
        self, name_or_path: Union[Path, str], content: Optional[str] = None,
    ) -> Path:
        if isinstance(name_or_path, Path):
            infile = name_or_path
        else:
            assert Path(name_or_path).name == name_or_path
            infile = self.input_dir / name_or_path
        if content:
            infile.write_text(self.dedent(content))
        else:
            infile.touch()
        return infile
