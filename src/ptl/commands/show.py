import logging
from pathlib import Path
from typing import Optional, Union

from ..infile import get_input_dir, read_infiles, sort_infiles


log = logging.getLogger(__name__)


def show(input_dir: Optional[Union[Path, str]] = None) -> None:
    input_dir = get_input_dir(input_dir)
    log.debug('input dir: %s', input_dir)
    for infile in sort_infiles(read_infiles(input_dir)):
        log.info('%s\n%s', infile, infile.render())
