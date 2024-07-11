import logging
from pathlib import Path
from typing import Iterable, Optional, Union

from ..infile import get_infiles, get_input_dir
from ..layer import Layer, LayerType, validate_layers


log = logging.getLogger(__name__)


def show(
    *,
    input_dir: Optional[Union[Path, str]] = None,
    layers: Optional[Iterable[Union[Path, str, Layer]]] = None,
    include_parent_layers: bool = True,
) -> None:
    input_dir = get_input_dir(input_dir)
    log.debug('input dir: %s', input_dir)
    if layers is not None:
        layers = validate_layers(
            layers, type_=LayerType.INFILE, input_dir=input_dir,
            check_type=False, check_exists=False,
        )
    for infile in get_infiles(
        input_dir, layers=layers, include_parent_layers=include_parent_layers,
    ):
        print('#', infile.generated_name)
        print(infile.render())
