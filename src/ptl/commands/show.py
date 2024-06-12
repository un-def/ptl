import logging
from pathlib import Path
from typing import Optional, Union

from ..infile import get_infiles, get_input_dir


log = logging.getLogger(__name__)


def show(input_dir: Optional[Union[Path, str]] = None) -> None:
    input_dir = get_input_dir(input_dir)
    log.debug('input dir: %s', input_dir)
    for infile in get_infiles(input_dir):
        print('#', infile)
        print(infile.render())
