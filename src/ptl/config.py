import logging
import os
import shlex
from functools import cached_property
from pathlib import Path
from typing import Any, List, Optional, Type, TypedDict, TypeVar, Union, cast

from ._error import Error
from .compat import toml_load
from .providers import Provider, Tool


log = logging.getLogger(__name__)


CONFIG_FILES = ('.ptl.toml', 'ptl.toml', 'pyproject.toml')


class ConfigError(Error):
    pass


CompileConfigDict = TypedDict(
    'CompileConfigDict', {'tool': str, 'tool-options': str}, total=False)
SyncConfigDict = TypedDict(
    'SyncConfigDict', {'tool': str, 'tool-options': str}, total=False)
ConfigDict = TypedDict('ConfigDict', {
    'compile': CompileConfigDict,
    'sync': SyncConfigDict,
    'directory': str,
    'tool': str,
    'tool-options': str,
}, total=False)


_CT = TypeVar('_CT', str, int, bool)


class Config:
    ENV_PREFIX = 'PTL_'

    _environ = os.environ

    _config_path: Optional[Path]
    _config_dict: ConfigDict

    def __init__(
        self, path: Optional[Union[Path, str]] = None, *,
        ignore_config_file: Optional[bool] = None,
    ) -> None:
        if ignore_config_file is None:
            ignore_config_file = self._get_env_value(bool, 'NO_CONFIG_FILE')
        if ignore_config_file:
            self._config_path = None
            self._config_dict = {}
            return
        if path is None:
            path = self._get_env_value(str, 'CONFIG_FILE')
            if path is None:
                path = find_config()
        if path is not None:
            path = Path(path).resolve()
            self._config_path = path
            self._config_dict = load_config(path) or {}
        else:
            self._config_path = None
            self._config_dict = {}

    @cached_property
    def directory(self) -> Optional[Path]:
        value = self._get_value(str, 'DIRECTORY', 'directory')
        if value is None:
            return None
        return Path(value).resolve()

    @cached_property
    def verbosity(self) -> int:
        value = self._get_value(int, 'VERBOSITY', 'verbosity')
        if value is None:
            return 0
        return value

    def get_tool(self, tool: Tool) -> Union[Provider, str, None]:
        if tool == Tool.COMPILE:
            return self._compile_tool
        if tool == Tool.SYNC:
            return self._sync_tool
        assert False, 'should not reach here'

    def get_tool_options(self, tool: Tool) -> Optional[List[str]]:
        if tool == Tool.COMPILE:
            return self._compile_tool_options
        elif tool == Tool.SYNC:
            return self._sync_tool_options
        assert False, 'should not reach here'

    @cached_property
    def _compile_tool(self) -> Union[Provider, str, None]:
        value = self._get_value(str, 'COMPILE_TOOL', 'compile.tool')
        if value is not None:
            return self._maybe_cast_tool_to_provider(value)
        return self._tool

    @cached_property
    def _sync_tool(self) -> Union[Provider, str, None]:
        value = self._get_value(str, 'SYNC_TOOL', 'sync.tool')
        if value is not None:
            return self._maybe_cast_tool_to_provider(value)
        return self._tool

    @cached_property
    def _tool(self) -> Union[Provider, str, None]:
        tool = self._get_value(str, 'TOOL', 'tool')
        if tool is None:
            return None
        return self._maybe_cast_tool_to_provider(tool)

    @cached_property
    def _compile_tool_options(self) -> Optional[List[str]]:
        value = self._get_value(
            str, 'COMPILE_TOOL_OPTIONS', 'compile.tool-options')
        if value is None:
            return None
        return shlex.split(value)

    @cached_property
    def _sync_tool_options(self) -> Optional[List[str]]:
        value = self._get_value(str, 'SYNC_TOOL_OPTIONS', 'sync.tool-options')
        if value is None:
            return None
        return shlex.split(value)

    def _maybe_cast_tool_to_provider(self, tool: str) -> Union[Provider, str]:
        if tool == ':pip-tools:':
            return Provider.PIP_TOOLS
        if tool == ':uv:':
            return Provider.UV
        return tool

    def _get_value(
        self, type_: Type[_CT], env_name: str, file_path: str,
    ) -> Optional[_CT]:
        env_value = self._get_env_value(type_, env_name)
        if env_value is not None:
            return env_value
        return self._get_file_value(type_, file_path)

    def _get_env_value(self, type_: Type[_CT], name: str) -> Optional[_CT]:
        var_name = f'{self.ENV_PREFIX}{name}'
        value = self._environ.get(var_name)
        if value is None:
            return None
        # issubclass(type_, bool) works with mypy, but not pyright
        if type_ is bool:
            value_lower = value.lower()
            if value_lower in ['1', 'true', 'yes', 'on']:
                return True   # type: ignore[return-value]
            if value_lower in ['0', 'false', 'no', 'off']:
                return False   # type: ignore[return-value]
            raise ConfigError(f'{var_name}: invalid bool value: {value!r}')
        try:
            return type_(value)
        except ValueError as exc:
            raise ConfigError(f'{var_name}: {exc}') from exc

    def _get_file_value(self, type_: Type[_CT], path: str) -> Optional[_CT]:
        obj: Any = self._config_dict   # type: ignore[misc]
        traversed_path: List[str] = []
        for key in path.split('.'):
            if not isinstance(obj, dict):
                raise ConfigError(
                    f'{self._config_path}: {".".join(traversed_path)} '
                    'must be a table, got '
                    f'{type(obj).__name__}'   # pyright: ignore
                )
            traversed_path.append(key)
            try:
                obj = obj[key]
            except KeyError:
                return None
        if not isinstance(obj, type_):
            raise ConfigError(
                f'{self._config_path}: {".".join(traversed_path)}: '
                f'{type_.__name__} expected, got {type(obj).__name__}'
            )
        return obj


def load_config(path: Union[Path, str]) -> Optional[ConfigDict]:
    if toml_load is None:
        log.debug('no toml parser found')
        raise ConfigError('no toml parser found')
    path = Path(path)
    if not path.exists():
        raise ConfigError(f'{path} does not exist')
    if not path.is_file():
        raise ConfigError(f'{path} is not a file')
    log.debug('loading config: %s', path)
    with open(path, 'rb') as fo:
        try:
            config = toml_load(fo)
        # {tomllib,tomli}.TOMLDecodeError are subclasses of ValueError
        except ValueError as exc:
            raise ConfigError(f'{path}: {exc}') from exc
    try:
        tool_config: Any = config['tool']   # type: ignore[misc]
    except KeyError:
        return None
    if not isinstance(tool_config, dict):
        raise ConfigError(
            f'{path}: tool must be a table, got {type(tool_config).__name__}')
    try:
        ptl_config: Any = tool_config['ptl']   # type: ignore[misc]
    except KeyError:
        return None
    if not isinstance(ptl_config, dict):
        raise ConfigError(
            f'{path}: tool.ptl must be a table, '
            f'got {type(ptl_config).__name__}'
        )
    return cast(ConfigDict, ptl_config)


def find_config() -> Optional[Path]:
    for config_file in CONFIG_FILES:
        path = Path(config_file)
        if path.exists() and path.is_file():
            return path.resolve()
    return None
