import logging
import subprocess
from pathlib import Path
from typing import Iterable, Optional, Union

from ..exceptions import Error
from ..infile import ReferenceType, get_infiles, get_input_dir
from ..providers import Tool, find_tool


log = logging.getLogger(__name__)


def compile(
    input_dir: Optional[Union[Path, str]] = None,
    compile_command_line: Optional[Iterable[Union[Path, str]]] = None,
) -> None:
    input_dir = get_input_dir(input_dir)
    log.debug('input dir: %s', input_dir)
    if not compile_command_line:
        compile_command_line, _ = find_tool(Tool.COMPILE)
    log.debug('using %s', compile_command_line)
    cwd = Path.cwd()
    for infile in get_infiles(input_dir):
        log.info('compiling %s', infile)
        output_file = (input_dir / infile.output_name).relative_to(cwd)
        with infile.temporarily_write_to(
            input_dir, references_as=ReferenceType.CONSTRAINTS,
        ) as input_file:
            compile_cmd = [
                *compile_command_line,
                input_file.relative_to(cwd),
                '-o', output_file,
            ]
            log.debug('calling %s', compile_cmd)
            try:
                subprocess.check_call(compile_cmd)
            except subprocess.CalledProcessError:
                raise Error
