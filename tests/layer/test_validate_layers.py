from pathlib import Path
from typing import Optional

import pytest

from ptl.exceptions import LayerFileError, LayerNameError, LayerTypeError
from ptl.layer import Layer, LayerType, validate_layers

from tests.testlib import InFileTestSuite


class TestSuite(InFileTestSuite):

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.monkeypatch = monkeypatch

    def chdir(self, directory: Optional[Path] = None) -> None:
        if not directory:
            directory = self.input_dir
        self.monkeypatch.chdir(directory)

    def test_parameters_assertion(self) -> None:
        with pytest.raises(AssertionError, match='check_type = True'):
            validate_layers([], check_type=True)

    def test_input_types(self, tmp_path: Path) -> None:
        self.chdir(tmp_path)
        self.create_file(tmp_path / 'tmp.in')
        self.create_file('main.txt')
        self.create_file('dev.in')

        layers = validate_layers(
            ('./tmp.in', 'main.txt', 'dev'),
            type_=LayerType.INFILE, input_dir=self.input_dir,
        )

        assert layers == [
            Layer(tmp_path / 'tmp.in'),
            Layer(self.input_dir / 'main.txt'),
            Layer(self.input_dir / 'dev.in'),
        ]

    def test_type_and_inpud_dir_are_optional(self) -> None:
        self.chdir()
        self.create_file('main.in')
        self.create_file('dev.requirements.txt')

        layers = validate_layers(
            ['./main.in', self.input_dir / 'dev.requirements.txt'])

        assert layers == [
            Layer(self.input_dir / 'main.in'),
            Layer(self.input_dir / 'dev.requirements.txt'),
        ]

    def test_check_type_ok(self) -> None:
        self.create_file('main.in')
        self.create_file('dev.in')

        layers = validate_layers(
            [self.input_dir / 'main.in', 'dev'],
            type_=LayerType.INFILE, check_type=True, input_dir=self.input_dir,
        )

        assert layers == [
            Layer(self.input_dir / 'main.in'),
            Layer(self.input_dir / 'dev.in'),
        ]

    def test_error_check_type(self) -> None:
        self.create_file('main.in')
        self.create_file('dev.txt')

        with pytest.raises(
            LayerTypeError, match=r'dev\.txt: infile expected, got lock',
        ):
            validate_layers(
                [self.input_dir / 'main.in', 'dev.txt'],
                type_=LayerType.INFILE, check_type=True,
                input_dir=self.input_dir,
            )

    def test_error_does_not_exist(self) -> None:
        self.create_file('main.in')

        with pytest.raises(LayerFileError, match=r'dev\.txt does not exist'):
            validate_layers(['main.in', 'dev.txt'], input_dir=self.input_dir)

    def test_error_cannot_infer_type(self) -> None:
        self.create_file('main.in')
        self.create_file('dev.in')

        with pytest.raises(LayerNameError, match=r'cannot infer type: dev'):
            validate_layers(['main.in', 'dev'], input_dir=self.input_dir)

    def test_error_cannot_locate(self) -> None:
        self.chdir()
        self.create_file('main.in')
        self.create_file('dev.in')

        with pytest.raises(
            LayerFileError, match=r'cannot locate layer.*: dev\.in',
        ):
            validate_layers(['./main.in', 'dev.in'])
