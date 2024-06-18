import logging
import subprocess
from pathlib import Path
from typing import Iterable, Optional, Union

from .._error import Error
from ..infile import ReferenceType, get_infiles, get_input_dir
from ..utils import try_relative_to


log = logging.getLogger(__name__)


class CompileError(Error):
    pass


def compile(
    command_line: Iterable[Union[Path, str]],
    input_dir: Optional[Union[Path, str]] = None,
) -> None:
    log.debug('using %s', command_line)
    input_dir = get_input_dir(input_dir)
    log.debug('input dir: %s', input_dir)
    cwd = Path.cwd()
    for infile in get_infiles(input_dir):
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
