from __future__ import annotations

import enum
import sys
from importlib import import_module
from typing import Any, BinaryIO, Callable, Dict, Optional


if sys.version_info >= (3, 11):
    StrEnum = enum.StrEnum
else:
    class StrEnum(str, enum.Enum):
        pass


toml_load: Optional[   # type: ignore[misc]
    Callable[[BinaryIO], Dict[str, Any]]] = None

if sys.version_info >= (3, 11):
    from tomllib import load as toml_load
else:
    try:
        toml_load = import_module('tomli').load
    except ImportError:
        pass


__all__ = [
    'toml_load',
    'StrEnum',
]
