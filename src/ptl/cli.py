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

    input_dir: Optional[str]
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
        '-d', '--directory', metavar='DIR', dest='input_dir',
        help='input directory',
    )

    logging_options = command_options.add_mutually_exclusive_group()
    logging_options.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='get more output',
    )
    logging_options.add_argument(
        '-q', '--quiet', action='count', default=0,
        help='get less output',
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
    args, tool_args = parser.parse_known_args(argv, namespace=Args())
    command = args.command
    if command not in Tool and tool_args:
        # only sync and compile accept extra args, other commands should raise
        # an error, the simplest way to do it is just call parse_args()
        parser.parse_args(argv)

    verbosity: int = 0
    verbosity_arg: Optional[str] = None
    if quiet := args.quiet:
        verbosity = -quiet
        verbosity_arg = '-{}'.format('q' * quiet)
    elif verbose := args.verbose:
        verbosity = verbose
        verbosity_arg = '-{}'.format('v' * verbose)
    configure_logging(verbosity)

    input_dir = args.input_dir

    if command in Tool:
        tool_command_line = get_tool_command_line(args)
        if verbosity_arg:
            tool_command_line.append(verbosity_arg)
        tool_command_line.extend(tool_args)
        if command == Tool.COMPILE:
            commands.compile(
                command_line=tool_command_line,
                input_dir=input_dir,
            )
        elif command == Tool.SYNC:
            commands.sync(
                command_line=tool_command_line,
                input_dir=input_dir,
            )
        else:
            assert False, 'should not reach here'
    elif command == 'show':
        commands.show(input_dir)
    else:
        assert False, 'should not reach here'


def configure_logging(verbosity: int) -> None:
    if verbosity > 0:
        log_level = logging.DEBUG
    elif verbosity < 0:
        log_level = logging.ERROR
    else:
        log_level = logging.INFO
    if log_level == logging.DEBUG:
        log_format = '[ %(asctime)s | %(name)s | %(levelname)s ] %(message)s'
    else:
        log_format = '%(message)s'
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
        log.debug('using %s %s', command_line, version)
    return command_line
