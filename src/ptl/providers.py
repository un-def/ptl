import dataclasses
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import ClassVar, Dict, Iterable, List, Tuple, Union

from ._error import Error
from .compat import StrEnum
from .utils import is_path


class ExecutableNotFound(Error):

    def __init__(
        self, name_or_path: Union[str, Path], message: str,
    ) -> None:
        self.name_or_path = name_or_path
        self.message = message

    def __str__(self) -> str:
        return f'{self.name_or_path} not found: {self.message}'


class ToolVersionCheckFailed(Error):
    pass


class ToolNotFound(Error):

    def __init__(self, tool: str, candidates: Iterable[str]) -> None:
        self.tool = tool
        self.candidates = tuple(candidates)

    def __str__(self) -> str:
        candidates = ', '.join(f'`{c}`' for c in self.candidates)
        return (
            f'{self.tool} tool not found, '
            f'candidates tried: {candidates}'
        )


class Tool(StrEnum):
    COMPILE = 'compile'
    SYNC = 'sync'


@dataclasses.dataclass(frozen=True)
class Provider:
    PIP_TOOLS: ClassVar['Provider']
    UV: ClassVar['Provider']

    tools: Dict[Tool, str]

    _registry: ClassVar[Dict[str, 'Provider']] = {}

    @classmethod
    def register(cls, attr_name: str, provider: 'Provider') -> None:
        setattr(cls, attr_name, provider)
        cls._registry[attr_name] = provider

    @classmethod
    def get_tool_candidates(cls, tool: Union[Tool, str]) -> Tuple[str, ...]:
        if not isinstance(tool, Tool):
            tool = Tool(tool)
        return tuple(prov.tools[tool] for prov in cls._registry.values())


Provider.register('PIP_TOOLS', Provider(
    tools={
        Tool.COMPILE: 'pip-compile',
        Tool.SYNC: 'pip-sync',
    },
))


Provider.register('UV', Provider(
    tools={
        Tool.COMPILE: 'uv pip compile',
        Tool.SYNC: 'uv pip sync',
    },
))


def find_executable(name_or_path: Union[Path, str]) -> Path:
    if isinstance(name_or_path, str):
        if not is_path(name_or_path):
            if _exec_path := shutil.which(name_or_path):
                return Path(_exec_path)
            raise ExecutableNotFound(name_or_path, 'not in PATH')
        name_or_path = Path(name_or_path)
    exec_path = name_or_path.resolve()
    if not exec_path.exists():
        raise ExecutableNotFound(exec_path, 'does not exist')
    if not exec_path.is_file():
        raise ExecutableNotFound(exec_path, 'not a file')
    return exec_path


def process_command_line(command_line: Union[Iterable[str], str]) -> List[str]:
    if isinstance(command_line, str):
        # XXX: won't properly work on Windows!
        command_line = shlex.split(command_line)
    else:
        command_line = list(command_line)
    command_line[0] = str(find_executable(command_line[0]))
    return command_line


def check_tool_version(
    command_line: Union[Iterable[str], str],
) -> Tuple[List[str], str]:
    try:
        command_line = process_command_line(command_line)
    except ExecutableNotFound as exc:
        raise ToolVersionCheckFailed from exc
    try:
        output = subprocess.check_output(
            [*command_line, '--version'], stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as exc:
        raise ToolVersionCheckFailed from exc
    return command_line, output.strip()


def find_tool(tool: Union[Tool, str]) -> Tuple[List[str], str]:
    candidates = Provider.get_tool_candidates(tool)
    for command_line in candidates:
        try:
            return check_tool_version(command_line)
        except ToolVersionCheckFailed:
            pass
    raise ToolNotFound(tool, candidates)
