import operator
import re
from contextlib import contextmanager
from pathlib import Path
from typing import (
    Any, Dict, Iterable, Iterator, List, Literal, Optional, Tuple, Union, cast,
)

from ._error import Error
from .compat import StrEnum


class InputDirectoryError(Error):
    pass


class ReferenceError(Error):
    pass


class UnknownReference(ReferenceError):
    pass


class CircularReference(ReferenceError):

    def __init__(self, infiles: Iterable['InFile']) -> None:
        self.infiles = tuple(infiles)

    def __str__(self) -> str:
        return ', '.join(map(str, self.infiles))


ReferenceTypeOrLiteral = Union['ReferenceType', Literal['r', 'c']]


class ReferenceType(StrEnum):
    REQUIREMENTS = 'r'
    CONSTRAINTS = 'c'

    @classmethod
    def cast(cls, value: ReferenceTypeOrLiteral) -> 'ReferenceType':
        if isinstance(value, cls):
            return value
        return cls(value)


class Reference:
    type: ReferenceType
    infile: 'InFile'

    def __init__(
        self, type: ReferenceTypeOrLiteral, infile: 'InFile',
    ) -> None:
        type = ReferenceType.cast(type)
        self.type = type
        self.infile = infile
        self._tuple = (type, infile)

    def __str__(self) -> str:
        return f'-{self.type} {self.infile.output_name}'

    def __repr__(self) -> str:   # pragma: no cover
        return f'{self.type.name.capitalize()}({self.infile})'

    def __eq__(self, other: Any) -> bool:   # type: ignore[misc]
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._tuple == other._tuple

    def __hash__(self) -> int:
        return hash(self._tuple)

    def copy_as(self, type: ReferenceTypeOrLiteral) -> 'Reference':
        type = ReferenceType.cast(type)
        return self.__class__(type, self.infile)


class InFile:
    original_name: str
    generated_name: str
    output_name: str
    stem: str
    references: List[Reference]
    dependencies: List[str]

    def __init__(self, name_or_path: Union[Path, str]) -> None:
        path = Path(name_or_path)
        self.stem = stem = path.stem
        self.original_name = path.name
        self.generated_name = f'{stem}.ptl.in'
        self.output_name = f'{stem}.txt'
        self.references = []
        self.dependencies = []

    def __str__(self) -> str:
        return self.original_name

    def __repr__(self) -> str:   # pragma: no cover
        return f'{self.__class__.__name__}({self})'

    def __eq__(self, other: Any) -> bool:   # type: ignore[misc]
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.original_name == other.original_name

    def __hash__(self) -> int:
        return hash(self.original_name)

    def add_reference(self, reference: Reference) -> None:
        self.references.append(reference)

    def iterate_references(
        self, *, recursive: bool,
        as_: Optional[ReferenceTypeOrLiteral] = None,
    ) -> Iterator[Reference]:
        if as_:
            as_ = ReferenceType.cast(as_)
        for ref in self.references:
            if as_:
                yield ref.copy_as(as_)
            else:
                yield ref
            if recursive:
                recursive_as: Optional[ReferenceType]
                if as_:
                    recursive_as = as_
                elif ref.type == ReferenceType.CONSTRAINTS:
                    recursive_as = ReferenceType.CONSTRAINTS
                else:
                    recursive_as = None
                yield from ref.infile.iterate_references(
                    recursive=True, as_=recursive_as)

    def add_dependency(self, dependency: str) -> None:
        self.dependencies.append(dependency.strip())

    def render(
        self, *, references_as: Optional[ReferenceTypeOrLiteral] = None,
    ) -> str:
        return ''.join(self._line_iter(references_as=references_as))

    def write_to(
        self, directory: Union[Path, str],
        *, references_as: Optional[ReferenceTypeOrLiteral] = None,
    ) -> Path:
        path = Path(directory) / self.generated_name
        with open(path, 'wt') as fobj:
            fobj.writelines(self._line_iter(references_as=references_as))
        return path

    @contextmanager
    def temporarily_write_to(
        self, directory: Union[Path, str],
        *, references_as: Optional[ReferenceTypeOrLiteral] = None,
    ) -> Iterator[Path]:
        path: Optional[Path] = None
        try:
            yield (path := self.write_to(
                directory, references_as=references_as))
        finally:
            if path is not None:
                path.unlink()

    def _line_iter(
        self, *, references_as: Optional[ReferenceTypeOrLiteral] = None,
    ) -> Iterator[str]:
        references = self.iterate_references(recursive=True)
        if references_as:
            references = (ref.copy_as(references_as) for ref in references)
        for reference in references:
            yield f'{reference}\n'
        for dependency in self.dependencies:
            yield f'{dependency}\n'


_INLINE_COMMENT_REGEX = re.compile(r'\s+#')
_REFERENCE_REGEX = re.compile(
    r'^-(?P<type>[rc])\s*(?P<stem>[\w.-]+?)(?:\.in|\.txt)?$')


def read_infiles(input_dir: Union[Path, str]) -> Tuple[InFile, ...]:
    input_dir = Path(input_dir)
    input_paths = tuple(input_dir.glob('*.in'))
    stems_to_infiles: Dict[str, InFile] = {
        (infile := InFile(path)).stem: infile for path in input_paths}
    for infile in stems_to_infiles.values():
        with open(input_dir / infile.original_name) as fobj:
            for line in fobj:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if comment_match := _INLINE_COMMENT_REGEX.search(line):
                    line = line[:comment_match.start()]
                ref_match = _REFERENCE_REGEX.fullmatch(line)
                if not ref_match:
                    infile.add_dependency(line)
                    continue
                ref_type = cast(Literal['r', 'c'], ref_match.group('type'))
                ref_stem: str = ref_match.group('stem')
                try:
                    ref_infile = stems_to_infiles[ref_stem]
                except KeyError:
                    raise UnknownReference(f'{infile}: {ref_stem}')
                ref = Reference(ref_type, ref_infile)
                infile.add_reference(ref)
    return tuple(stems_to_infiles.values())


def sort_infiles(infiles: Iterable[InFile]) -> List[InFile]:
    sorted_infiles: List[InFile] = []
    _infiles_with_refs: Dict[InFile, List[Reference]] = {
        infile: infile.references for infile in infiles}
    while True:
        _processed = {
            infile for infile, refs in _infiles_with_refs.items() if not refs}
        if not _processed:
            break
        sorted_infiles.extend(
            sorted(_processed, key=operator.attrgetter('stem')))
        _infiles_with_refs = {
            infile: [ref for ref in refs if ref.infile not in _processed]
            for infile, refs in _infiles_with_refs.items()
            if infile not in _processed
        }
    if len(_infiles_with_refs) != 0:
        raise CircularReference(_infiles_with_refs)
    return sorted_infiles


def get_infiles(input_dir: Union[Path, str]) -> List[InFile]:
    infiles = read_infiles(input_dir)
    if not infiles:
        raise InputDirectoryError('no *.in files')
    return sort_infiles(infiles)


def get_input_dir(input_dir: Optional[Union[Path, str]] = None) -> Path:
    if input_dir:
        input_dir = Path(input_dir)
        if not input_dir.exists():
            raise InputDirectoryError(f'{input_dir} does not exist')
        if not input_dir.is_dir():
            raise InputDirectoryError(f'{input_dir} is not a directory')
    else:
        input_dir = Path('requirements')
        if not input_dir.is_dir():
            input_dir = Path('.')
            if not next(input_dir.glob('*.in'), None):
                raise InputDirectoryError('input directory not found')
    return input_dir.resolve()
