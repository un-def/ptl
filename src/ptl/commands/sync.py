import logging
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Union

from .._error import Error
from ..infile import get_infiles, get_input_dir


log = logging.getLogger(__name__)


class SyncError(Error):
    pass


def sync(
    command_line: Iterable[Union[Path, str]],
    input_dir: Optional[Union[Path, str]] = None,
) -> None:
    log.debug('using %s', command_line)
    input_dir = get_input_dir(input_dir)
    log.debug('input dir: %s', input_dir)
    cwd = Path.cwd()
    compiled_files: List[Path] = []
    missing_files: List[str] = []
    for infile in get_infiles(input_dir):
        output_name = infile.output_name
        compiled_file = input_dir / output_name
        if compiled_file.exists():
            try:
                compiled_file = compiled_file.relative_to(cwd)
            except ValueError:
                pass
            compiled_files.append(compiled_file)
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
