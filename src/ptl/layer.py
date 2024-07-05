import re
from pathlib import Path
from typing import (
    Any, Dict, Iterable, List, Literal, Optional, Tuple, Union, cast,
)

from ._error import Error
from .compat import StrEnum
from .utils import is_path


class LayerError(Error):
    pass


class LayerNameError(LayerError):
    pass


class LayerTypeError(LayerError):
    pass


class LayerFileError(LayerError):
    pass


class LayerType(StrEnum):
    INFILE = 'infile'
    LOCK = 'lock'


LayerExtension = Literal['.in', '.txt']


LAYER_TYPE_TO_EXTENSION: Dict[LayerType, LayerExtension] = {
    LayerType.INFILE: '.in',
    LayerType.LOCK: '.txt',
}

LAYER_EXTENSION_TO_TYPE: Dict[LayerExtension, LayerType] = {
    v: k for k, v in LAYER_TYPE_TO_EXTENSION.items()}


LAYER_NAME_REGEX = re.compile(
    r'(?P<stem>\w[\w.-]*?)(?P<suffix>\.requirements)?(?P<ext>\.in|\.txt)?')


class Layer:
    type: LayerType
    name: str
    path: Path
    stem: str
    has_requirements_suffix: bool
    extension: LayerExtension

    def __init__(
        self, name_or_path: Union[Path, str],
        type_: Optional[LayerType] = None, *,
        input_dir: Optional[Union[Path, str]] = None,
        check_exists: bool = True,
    ) -> None:
        path: Optional[Path]
        name: str
        if isinstance(name_or_path, str):
            if is_path(name_or_path):
                path = Path(name_or_path)
                name = path.name
            else:
                path = None
                name = name_or_path
        else:
            path = name_or_path
            name = path.name

        if not (match_ := LAYER_NAME_REGEX.fullmatch(name)):
            raise LayerNameError(f'invalid format: {name}')

        stem, suffix, ext = match_.groups()
        self.stem = stem

        if ext:
            is_bare_stem = False
            self.name = name
            self.has_requirements_suffix = bool(suffix)
        elif path or suffix:
            # if the passed value is a path, it must have a full name
            # if the passed value is a name with suffix, it must be a full name
            raise LayerNameError(f'extension required: {name}')
        else:
            # if the passed value is a bare stem, we compute `name` and
            # `has_requirements_suffix` values later
            is_bare_stem = True

        if ext:
            ext = cast(LayerExtension, ext)
            self.extension = ext
            self.type = LAYER_EXTENSION_TO_TYPE[ext]
        elif type_:
            ext = LAYER_TYPE_TO_EXTENSION[type_]
            self.extension = ext
            self.type = type_
        else:
            raise LayerNameError(f'cannot infer type: {name}')

        if path:
            path = path.resolve()
            if check_exists:
                self._check_exists(path)
            self.path = path
            return

        if not input_dir:
            raise LayerFileError(
                f'cannot locate layer file without input directory: {name}')
        input_dir = Path(input_dir).resolve()

        if is_bare_stem:
            candidates: List[Tuple[str, bool]] = [
                (f'{stem}.requirements{ext}', True),
                (f'{stem}{ext}', False),
            ]
            if self.type == LayerType.LOCK:
                candidates.append((f'{stem}.requirements.in', True))
                candidates.append((f'{stem}.in', False))
            for name, has_requirements_suffix in candidates:
                path = input_dir / name
                if self._check_exists(path, raise_exception=False):
                    path = path.with_suffix(self.extension)
                    self.name = path.name
                    self.has_requirements_suffix = has_requirements_suffix
                    break
            else:
                raise LayerNameError(f'cannot infer name: {stem}')
        else:
            path = input_dir / name

        if check_exists:
            self._check_exists(path)
        self.path = path

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:   # pragma: no cover
        return f'{self.__class__.__name__}({self.type.name}: {self})'

    def __eq__(self, other: Any) -> bool:   # type: ignore[misc]
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.path == other.path

    def __hash__(self) -> int:
        return hash(self.path)

    def _check_exists(
        self, path: Path, *, raise_exception: bool = True,
    ) -> bool:
        if not path.exists():
            if raise_exception:
                raise LayerFileError(f'{path} does not exist')
            return False
        if not path.is_file():
            if raise_exception:
                raise LayerFileError(f'{path} is not a file')
            return False
        return True


def validate_layers(
    layers: Iterable[Union[Path, str, Layer]],
    type_: Optional[LayerType] = None, *,
    input_dir: Optional[Union[Path, str]] = None,
    check_type: bool = False,
) -> List[Layer]:
    assert not (check_type and not type_), 'check_type = True requires type_'
    processed: List[Layer] = []
    for layer in layers:
        if not isinstance(layer, Layer):
            layer = Layer(layer, type_, input_dir=input_dir)
        if check_type and layer.type != type_:
            raise LayerTypeError(
                f'{layer}: {type_} expected, got {layer.type}')
        processed.append(layer)
    return processed
