import logging
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Union

from .._error import Error
from ..infile import get_infiles, get_input_dir
from ..providers import Tool, find_tool


log = logging.getLogger(__name__)


class SyncError(Error):
    pass


def sync(
    input_dir: Optional[Union[Path, str]] = None,
    sync_command_line: Optional[Iterable[Union[Path, str]]] = None,
) -> None:
    input_dir = get_input_dir(input_dir)
    log.debug('input dir: %s', input_dir)
    if not sync_command_line:
        sync_command_line, _ = find_tool(Tool.SYNC)
    log.debug('using %s', sync_command_line)
    cwd = Path.cwd()
    compiled_files: List[Path] = []
    missing_files: List[str] = []
    for infile in get_infiles(input_dir):
        output_name = infile.output_name
        compiled_file = input_dir / output_name
        if compiled_file.exists():
            compiled_files.append(compiled_file.relative_to(cwd))
        else:
            missing_files.append(output_name)
    if missing_files:
        raise SyncError(
            f'not all files are compiled, missing: {missing_files}')
    log.debug('syncing %s', compiled_files)
    sync_cmd = [
        *sync_command_line,
        *compiled_files,
    ]
    log.debug('calling %s', sync_cmd)
    try:
        subprocess.check_call(sync_cmd)
    except subprocess.CalledProcessError as exc:
        raise SyncError from exc
