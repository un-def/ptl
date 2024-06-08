import logging
from pathlib import Path
from typing import Optional, Union

from ..infile import get_requirements_dir, read_infiles, sort_infiles


log = logging.getLogger(__name__)


def show(requirements_dir: Optional[Union[Path, str]] = None) -> None:
    requirements_dir = get_requirements_dir(requirements_dir)
    log.debug('requirements dir: %s', requirements_dir)
    for infile in sort_infiles(read_infiles(requirements_dir)):
        log.info('%s\n%s', infile, infile.render())
