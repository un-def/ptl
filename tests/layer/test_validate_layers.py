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

    def test_check_type_required_if_type_is_set(self) -> None:
        with pytest.raises(TypeError, match='type_ requires check_type'):
            validate_layers(
                [], type_=LayerType.INFILE,   # type: ignore[call-overload]
                check_exists=False,
            )

    def test_check_type_true_not_allowed_if_type_is_not_set(self) -> None:
        with pytest.raises(TypeError, match='check_type=True requires type_'):
            validate_layers(
                [], check_type=True,   # type: ignore[call-overload]
                check_exists=False,
            )

    def test_input_types_without_type_check(self, tmp_path: Path) -> None:
        self.chdir(tmp_path)
        self.create_file(tmp_path / 'tmp.in')
        self.create_file('main.txt')
        self.create_file('dev.in')

        layers = validate_layers(
            ('./tmp.in', 'main.txt', 'dev'),
            type_=LayerType.INFILE, input_dir=self.input_dir,
            check_exists=True, check_type=False,
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
            ['./main.in', self.input_dir / 'dev.requirements.txt'],
            check_exists=True,
        )

        assert layers == [
            Layer(self.input_dir / 'main.in'),
            Layer(self.input_dir / 'dev.requirements.txt'),
        ]

    def test_check_type(self) -> None:
        self.create_file('main.in')
        self.create_file('dev.in')

        layers = validate_layers(
            [self.input_dir / 'main.in', 'dev'],
            type_=LayerType.INFILE, input_dir=self.input_dir,
            check_exists=True, check_type=True,
        )

        assert layers == [
            Layer(self.input_dir / 'main.in'),
            Layer(self.input_dir / 'dev.in'),
        ]

    def test_do_not_check_exists(self) -> None:
        self.create_file('main.requirements.in')
        self.create_file('dev.requirements.in')

        layers = validate_layers(
            [self.input_dir / 'main.in', 'dev'],
            type_=LayerType.LOCK, input_dir=self.input_dir,
            check_exists=False, check_type=False,
        )

        assert layers == [
            Layer(self.input_dir / 'main.in', check_exists=False),
            Layer(self.input_dir / 'dev.requirements.txt', check_exists=False),
        ]

    def test_error_unexpected_type(self) -> None:
        self.create_file('main.in')
        self.create_file('dev.txt')

        with pytest.raises(
            LayerTypeError, match=r'dev\.txt: infile expected, got lock',
        ):
            validate_layers(
                [self.input_dir / 'main.in', 'dev.txt'],
                type_=LayerType.INFILE, input_dir=self.input_dir,
                check_exists=True, check_type=True,
            )

    def test_error_does_not_exist(self) -> None:
        self.create_file('main.in')

        with pytest.raises(LayerFileError, match=r'dev\.txt does not exist'):
            validate_layers(
                ['main.in', 'dev.txt'], input_dir=self.input_dir,
                check_exists=True,
            )

    def test_error_cannot_infer_type(self) -> None:
        self.create_file('main.in')
        self.create_file('dev.in')

        with pytest.raises(LayerNameError, match=r'cannot infer type: dev'):
            validate_layers(
                ['main.in', 'dev'], input_dir=self.input_dir,
                check_exists=True,
            )

    def test_error_cannot_locate(self) -> None:
        self.chdir()
        self.create_file('main.in')
        self.create_file('dev.in')

        with pytest.raises(
            LayerFileError, match=r'cannot locate layer.*: dev\.in',
        ):
            validate_layers(
                ['./main.in', 'dev.in'], check_exists=True)
