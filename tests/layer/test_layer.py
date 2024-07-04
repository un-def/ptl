from pathlib import Path
from typing import Union

import pytest

from ptl.exceptions import LayerFileError, LayerNameError
from ptl.infile import InFile
from ptl.layer import Layer, LayerType

from tests.testlib import InFileTestSuite


class TestSuite(InFileTestSuite):

    def test_equal(self) -> None:
        self.create_file('main.in')

        layer_1 = Layer('main.in', input_dir=self.input_dir)
        layer_2 = Layer(self.input_dir / 'main.in')

        assert layer_1 == layer_2
        assert hash(layer_1) == hash(layer_2)

    def test_not_equal_ext(self) -> None:
        self.create_file('main.in')
        self.create_file('main.txt')

        layer_1 = Layer('main.in', input_dir=self.input_dir)
        layer_2 = Layer('main.txt', input_dir=self.input_dir)

        assert layer_1 != layer_2
        assert hash(layer_1) != hash(layer_2)

    def test_not_equal_suffix(self) -> None:
        self.create_file('main.in')
        self.create_file('main.requirements.in')

        layer_1 = Layer('main.in', input_dir=self.input_dir)
        layer_2 = Layer('main.requirements.in', input_dir=self.input_dir)

        assert layer_1 != layer_2
        assert hash(layer_1) != hash(layer_2)

    def test_not_equal_path(self, tmp_path: Path) -> None:
        self.create_file('main.in')
        self.create_file(tmp_path / 'main.in')

        layer_1 = Layer('main.in', input_dir=self.input_dir)
        layer_2 = Layer(tmp_path / 'main.in')

        assert layer_1 != layer_2
        assert hash(layer_1) != hash(layer_2)

    def test_not_equal_other_is_not_layer(self) -> None:
        self.create_file('main.in')

        layer = Layer(self.input_dir / 'main.in')
        infile = InFile(self.input_dir / 'main.in')

        assert layer != infile

    @pytest.mark.parametrize('path', ['./main.in', Path('main.in')])
    def test_rel_path(
        self, monkeypatch: pytest.MonkeyPatch, path: Union[Path, str],
    ) -> None:
        monkeypatch.chdir(self.input_dir)
        self.create_file('main.in')

        layer = Layer(path)

        assert layer.type == LayerType.INFILE
        assert layer.name == 'main.in'
        assert layer.path == self.input_dir / 'main.in'
        assert layer.stem == 'main'
        assert layer.has_requirements_suffix is False
        assert layer.extension == '.in'

    @pytest.mark.parametrize('as_str', [False, True])
    def test_abs_path(self, as_str: bool) -> None:
        self.create_file('main.requirements.txt')
        path: Union[Path, str] = self.input_dir / 'main.requirements.txt'
        if as_str:
            path = str(path)

        layer = Layer(path)

        assert layer.type == LayerType.LOCK
        assert layer.name == 'main.requirements.txt'
        assert layer.path == self.input_dir / 'main.requirements.txt'
        assert layer.stem == 'main'
        assert layer.has_requirements_suffix is True
        assert layer.extension == '.txt'

    def test_name(self) -> None:
        self.create_file('dev.requirements.in')

        layer = Layer('dev.requirements.in', input_dir=self.input_dir)

        assert layer.type == LayerType.INFILE
        assert layer.name == 'dev.requirements.in'
        assert layer.path == self.input_dir / 'dev.requirements.in'
        assert layer.stem == 'dev'
        assert layer.has_requirements_suffix is True
        assert layer.extension == '.in'

    def test_stem_without_suffix(self) -> None:
        self.create_file('dev.in')

        layer = Layer('dev', LayerType.INFILE, input_dir=self.input_dir)

        assert layer.type == LayerType.INFILE
        assert layer.name == 'dev.in'
        assert layer.path == self.input_dir / 'dev.in'
        assert layer.stem == 'dev'
        assert layer.has_requirements_suffix is False
        assert layer.extension == '.in'

    def test_stem_with_suffix(self) -> None:
        self.create_file('dev.requirements.txt')

        layer = Layer('dev', LayerType.LOCK, input_dir=self.input_dir)

        assert layer.type == LayerType.LOCK
        assert layer.name == 'dev.requirements.txt'
        assert layer.path == self.input_dir / 'dev.requirements.txt'
        assert layer.stem == 'dev'
        assert layer.has_requirements_suffix is True
        assert layer.extension == '.txt'

    @pytest.mark.parametrize('name_or_path', [Path('./main.in'), 'main.in'])
    def test_type_ignored_if_inferred(
        self, monkeypatch: pytest.MonkeyPatch, name_or_path: Union[Path, str],
    ) -> None:
        monkeypatch.chdir(self.input_dir)
        self.create_file('main.in')

        layer = Layer(name_or_path, LayerType.LOCK, input_dir=self.input_dir)

        assert layer.type == LayerType.INFILE
        assert layer.name == 'main.in'
        assert layer.extension == '.in'

    @pytest.mark.parametrize('path', [Path('./main.in'), './main.in'])
    def test_input_dir_ignored_if_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        path: Union[Path, str],
    ) -> None:
        monkeypatch.chdir(self.input_dir)
        self.create_file('main.in')

        layer = Layer(path, input_dir=tmp_path)

        assert layer.path == self.input_dir / 'main.in'

    @pytest.mark.parametrize('name_or_path', [
        Path('/path/to/!main.in'), '.in', '.', '',
    ])
    def test_error_invalid_format(
        self, name_or_path: Union[Path, str],
    ) -> None:
        with pytest.raises(LayerNameError, match='invalid format'):
            Layer(name_or_path)

    @pytest.mark.parametrize('name_or_path', [
        Path('/path/to/main'), './dev.requirements', 'dev.requirements',
    ])
    def test_error_extension_required(
        self, name_or_path: Union[Path, str],
    ) -> None:
        with pytest.raises(LayerNameError, match='extension required'):
            Layer(name_or_path)

    def test_error_cannot_infer_type(self) -> None:
        with pytest.raises(LayerNameError, match='cannot infer type'):
            Layer('test')

    def test_error_cannot_locate(self) -> None:
        with pytest.raises(LayerFileError, match='cannot locate layer'):
            Layer('test', LayerType.INFILE)

    def test_error_does_not_exist_path(self) -> None:
        with pytest.raises(LayerFileError, match='does not exist'):
            Layer(self.input_dir / 'does-not-exist.in')

    def test_error_does_not_exist_name(self) -> None:
        with pytest.raises(LayerFileError, match='does not exist'):
            Layer('does-not-exist.in', input_dir=self.input_dir)

    def test_error_not_a_file_path(self) -> None:
        (self.input_dir / 'is-dir.in').mkdir()

        with pytest.raises(LayerFileError, match='not a file'):
            Layer(self.input_dir / 'is-dir.in')

    def test_error_not_a_file_name(self) -> None:
        (self.input_dir / 'is-dir.in').mkdir()

        with pytest.raises(LayerFileError, match='not a file'):
            Layer('is-dir.in', input_dir=self.input_dir)
