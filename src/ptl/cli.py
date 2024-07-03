import argparse
import logging
import sys
from typing import TYPE_CHECKING, List, Optional, Sequence

from . import __version__, commands
from .exceptions import Error
from .providers import (
    Provider, Tool, check_tool_version, find_tool, process_command_line,
)


log = logging.getLogger(__name__)


# type aliases
Parser = argparse.ArgumentParser
if TYPE_CHECKING:
    # See: https://github.com/python/cpython/issues/101503
    SubParsers = argparse._SubParsersAction[Parser]   # pyright: ignore


class Args(argparse.Namespace):
    command: str

    use_uv: bool
    use_pip_tools: bool
    custom_tool: Optional[str]

    input_dir: Optional[str]
    verbose: int
    quiet: int


def add_command_parser(
    subparsers: 'SubParsers',
    command: str, add_tool_selection: bool = True,
    add_tool_options_to_usage: bool = True,
) -> None:
    parser = subparsers.add_parser(
        command, add_help=False,
        help=f'{command} requirements',
    )

    logging_options = parser.add_argument_group('logging options')
    logging_verbosity = logging_options.add_mutually_exclusive_group()
    logging_verbosity.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='get more output',
    )
    logging_verbosity.add_argument(
        '-q', '--quiet', action='count', default=0,
        help='get less output',
    )

    if add_tool_selection:
        _tool_selection = parser.add_argument_group('tool selection')
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

    command_options = parser.add_argument_group(f'{command} options')
    command_options.add_argument(
        '-d', '--directory', metavar='DIR', dest='input_dir',
        help='input directory',
    )

    general_options = parser.add_argument_group('general options')

    # since we don't want to include [-h] so as not to clutter the usage line,
    # we format the usage before adding the help argument
    usage = parser.format_usage()
    if add_tool_options_to_usage:
        usage = f'{usage.rstrip()} [{command.upper()} OPTIONS ...]\n'
    parser.usage = usage

    general_options.add_argument(
        '-h', '--help', action='help',
        help='show this help message and exit',
    )


def build_parser() -> Parser:
    parser = argparse.ArgumentParser(prog='ptl', add_help=False)
    general_options = parser.add_argument_group('general options')
    general_options.add_argument(
        '-h', '--help', action='help',
        help='show this help message and exit',
    )
    general_options.add_argument(
        '-V', '--version', action='version', version=__version__,
        help='show version and exit',
    )
    subparsers = parser.add_subparsers(
        title='Commands', required=True, dest='command', metavar='COMMAND')
    add_command_parser(subparsers, 'compile')
    add_command_parser(subparsers, 'sync')
    add_command_parser(
        subparsers, 'show',
        add_tool_selection=False, add_tool_options_to_usage=False,
    )
    return parser


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

    is_tool: bool
    try:
        Tool(command)
    except ValueError:
        is_tool = False
    else:
        is_tool = True

    if not is_tool and tool_args:
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

    if is_tool:
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
