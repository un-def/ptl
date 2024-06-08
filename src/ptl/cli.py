import argparse
import logging
import sys
from typing import List, Optional, Sequence

from . import __version__, commands
from .exceptions import Error
from .providers import (
    Provider, Tool, check_tool_version, find_tool, process_command_line,
)


log = logging.getLogger(__name__)


class Args(argparse.Namespace):
    command: str

    use_uv: bool
    use_pip_tools: bool
    custom_tool: Optional[str]

    requirements_dir: Optional[str]
    verbose: int
    quiet: int


def add_command_options(
    command: str, command_parser: argparse.ArgumentParser,
    add_tool_selection: bool = True,
) -> None:
    if add_tool_selection:
        _tool_selection = command_parser.add_argument_group('tool selection')
        tool_selection = _tool_selection.add_mutually_exclusive_group()
        tool_selection.add_argument(
            '--pip-tools', action='store_true', dest='use_pip_tools',
            help=f'use `pip-{command}`',
        )
        tool_selection.add_argument(
            '--uv', action='store_true', dest='use_uv',
            help=f'use `uv pip {command}`',
        )
        tool_selection.add_argument(
            '--tool', metavar='TOOL', dest='custom_tool',
            help='use custom tool',
        )

    command_options = command_parser.add_argument_group(f'{command} options')
    command_options.add_argument(
        '-d', '--directory', metavar='DIR', dest='requirements_dir',
        help='requirements directory',
    )

    logging_options = command_options.add_mutually_exclusive_group()
    logging_options.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='get more output',
    )
    logging_options.add_argument(
        '-q', '--quiet', action='count', default=0,
        help='get less output, can be used up to 3 times',
    )

    general_options = command_parser.add_argument_group('general options')
    general_options.add_argument(
        '-h', '--help', action='help',
        help='show this help message and exit',
    )


def build_parser() -> argparse.ArgumentParser:
    root_parser = argparse.ArgumentParser(prog='ptl', add_help=False)
    root_general_options = root_parser.add_argument_group('general options')
    root_general_options.add_argument(
        '-h', '--help', action='help',
        help='show this help message and exit',
    )
    root_general_options.add_argument(
        '-V', '--version', action='version', version=__version__,
        help='show version and exit',
    )

    subparsers = root_parser.add_subparsers(
        title='Commands', required=True, dest='command', metavar='COMMAND')

    compile_parser = subparsers.add_parser(
        'compile', add_help=False,
        help='compile requirements',
    )
    add_command_options('compile', compile_parser)

    sync_parser = subparsers.add_parser(
        'sync', add_help=False,
        help='sync requirements',
    )
    add_command_options('sync', sync_parser)

    show_parser = subparsers.add_parser(
        'show', add_help=False,
        help='show requirements',
    )
    add_command_options('show', show_parser, add_tool_selection=False)

    return root_parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    try:
        do_main(argv)
    except Error as exc:
        log.error('%s: %s', exc.__class__.__name__, exc)
        sys.exit(1)


def do_main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv, namespace=Args())

    if quiet := args.quiet:
        verbosity = -quiet
    elif verbose := args.verbose:
        verbosity = verbose
    else:
        verbosity = 0
    configure_logging(verbosity)

    requirements_dir = args.requirements_dir
    command = args.command

    if command in Tool:
        tool_command_line = get_tool_command_line(args)
        if command == Tool.COMPILE:
            commands.compile(
                requirements_dir=requirements_dir,
                compile_command_line=tool_command_line,
            )
        elif command == Tool.SYNC:
            raise NotImplementedError
        else:
            assert False, 'should not reach here'
    elif command == 'show':
        commands.show(requirements_dir)
    else:
        assert False, 'should not reach here'


def configure_logging(verbosity: int) -> None:
    if verbosity >= 1:
        log_level = logging.DEBUG
    elif verbosity == 0:
        log_level = logging.INFO
    elif verbosity == -1:
        log_level = logging.WARNING
    elif verbosity == -2:
        log_level = logging.ERROR
    elif verbosity <= -3:
        log_level = logging.CRITICAL
    else:
        assert False, 'should not reach here'
    if log_level == logging.DEBUG:
        log_format = '[ %(asctime)s | %(name)s | %(levelname)s ] %(message)s'
    else:
        log_format = '*** %(message)s'
    logging.basicConfig(
        level=log_level, format=log_format, datefmt='%d-%m-%Y %H:%M:%S')


def get_tool_command_line(args: Args) -> List[str]:
    tool = Tool(args.command)
    if command_line_str := args.custom_tool:
        command_line = process_command_line(command_line_str)
    else:
        provider: Optional[Provider] = None
        if args.use_pip_tools:
            provider = Provider.PIP_TOOLS
        elif args.use_uv:
            provider = Provider.UV
        if provider:
            command_line_str = provider.tools[tool]
            command_line, version = check_tool_version(command_line_str)
        else:
            command_line, version = find_tool(tool)
        log.debug('using %s version %s', command_line, version)
    return command_line
