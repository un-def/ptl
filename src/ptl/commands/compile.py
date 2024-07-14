import logging
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Union

from .._error import Error
from ..infile import ReferenceType, get_infiles, get_input_dir
from ..layer import Layer, LayerType, validate_layers
from ..utils import try_relative_to


log = logging.getLogger(__name__)


class CompileError(Error):
    pass


def compile(
    command_line: Iterable[Union[Path, str]], *,
    input_dir: Optional[Union[Path, str]] = None,
    layers: Optional[Iterable[Union[Path, str, Layer]]] = None,
    include_parent_layers: bool = True,
) -> None:
    log.debug('using %s', command_line)
    input_dir = get_input_dir(input_dir)
    log.debug('input dir: %s', input_dir)
    if layers is not None:
        layers = validate_layers(
            layers, type_=LayerType.INFILE, input_dir=input_dir,
            check_exists=True, check_type=False,
        )
    infiles = get_infiles(
        input_dir, layers=layers, include_parent_layers=include_parent_layers)
    if not include_parent_layers:
        locks_to_compile = {infile.output_name for infile in infiles}
        missing_locks: List[str] = []
        for infile in infiles:
            for ref in infile.iterate_references(recursive=True):
                lock = ref.infile.output_name
                if (
                    lock not in locks_to_compile
                    and not (input_dir / lock).exists()
                ):
                    missing_locks.append(lock)
        if missing_locks:
            raise CompileError(
                'not all referenced layers are compiled, '
                f'missing: {", ".join(missing_locks)}'
            )
    cwd = Path.cwd()
    for infile in infiles:
        log.info('compiling %s', infile)
        output_file = try_relative_to(input_dir / infile.output_name, cwd)
        with infile.temporarily_write_to(
            input_dir, references_as=ReferenceType.CONSTRAINTS,
        ) as input_file:
            cmd = [
                *command_line,
                try_relative_to(input_file, cwd),
                '-o', output_file,
            ]
            log.debug('calling %s', cmd)
            try:
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as exc:
                raise CompileError from exc
