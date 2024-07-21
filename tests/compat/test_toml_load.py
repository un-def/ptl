import importlib
import sys
from types import ModuleType
from typing import Iterator
from unittest.mock import Mock

import pytest


@pytest.fixture
def compat_module() -> Iterator[ModuleType]:
    from ptl import compat
    importlib.reload(compat)
    try:
        yield compat
    finally:
        importlib.reload(compat)


@pytest.mark.skipif(sys.version_info >= (3, 11), reason='Python >= 3.11')
def test_python_lt_311(compat_module: ModuleType) -> None:
    import tomli  # pyright: ignore[reportMissingModuleSource]

    assert compat_module.toml_load is tomli.load


@pytest.mark.skipif(sys.version_info >= (3, 11), reason='Python >= 3.11')
def test_python_lt_311_no_tomli(
    monkeypatch: pytest.MonkeyPatch, compat_module: ModuleType,
) -> None:
    import_module_mock = Mock(
        spec_set=importlib.import_module, side_effect=ImportError)

    with monkeypatch.context() as mp:
        mp.setattr(importlib, 'import_module', import_module_mock)
        importlib.reload(compat_module)

    assert compat_module.toml_load is None


@pytest.mark.skipif(sys.version_info < (3, 11), reason='Python < 3.11')
def test_python_ge_311(compat_module: ModuleType) -> None:
    import tomllib  # type: ignore[import-not-found]

    assert compat_module.toml_load is tomllib.load
    with pytest.raises(ImportError):
        import tomli as tomli  # pyright: ignore[reportMissingModuleSource]
