import logging
import subprocess
from pathlib import Path
from typing import Iterable, List, Literal, Optional, Union

from .._error import Error
from ..infile import ReferenceType, get_infiles, get_input_dir
from ..layer import Layer, LayerType, validate_layers
from ..utils import try_relative_to


log = logging.getLogger(__name__)


class SyncError(Error):
    pass


def sync(
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
            # we check for infiles here, not locks, since we do a lock files
            # check later; here we only want to check if layer exists
            layers, type_=LayerType.INFILE, input_dir=input_dir,
            check_exists=True, check_type=False,
        )
    _include_parent_layers: Literal[ReferenceType.REQUIREMENTS, False] = (
        ReferenceType.REQUIREMENTS if include_parent_layers else False)
    infiles = get_infiles(
        input_dir, layers=layers, include_parent_layers=_include_parent_layers)
    cwd = Path.cwd()
    compiled_files: List[Path] = []
    missing_files: List[str] = []
    for infile in infiles:
        output_name = infile.output_name
        compiled_file = input_dir / output_name
        if compiled_file.exists():
            compiled_files.append(try_relative_to(compiled_file, cwd))
        else:
            missing_files.append(output_name)
    if missing_files:
        raise SyncError(
            f'not all files are compiled, missing: {", ".join(missing_files)}')
    log.debug('syncing %s', compiled_files)
    cmd = [
        *command_line,
        *compiled_files,
    ]
    log.debug('calling %s', cmd)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        raise SyncError from exc
