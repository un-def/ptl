import sys
from typing import Any, Dict, List

import pytest

from ptl.cli import Args, build_parser, parse_args


DEFAULTS: Dict[str, Any] = dict(   # type: ignore[misc]
    verbose=0,
    quiet=0,
    config_path=None,
    no_config=None,
    use_uv=False,
    use_pip_tools=False,
    custom_tool=None,
    directory=None,
    layers=list,
    include_parent_layers=True,
    extra_args=list,
)


def set_defaults(args: Args) -> None:
    for key, value in DEFAULTS.items():
        try:
            getattr(args, key)
            continue
        except AttributeError:
            pass
        if callable(value):
            value = value()
        setattr(args, key, value)


@pytest.mark.parametrize(['args', 'expected_extra_args', 'expected_args'], [
    pytest.param(
        ['compile'], [],
        Args(command='compile'),
        id='no-args',
    ),
    pytest.param(
        ['compile', '--only', 'dev', 'main'], [],
        Args(
            command='compile',
            layers=['dev', 'main'],
            include_parent_layers=False,
        ),
        id='only-layers-no-extra',
    ),
    pytest.param(
        ['compile', '-v', 'dev', 'main', '-P', 'tox'], ['-P', 'tox'],
        Args(
            command='compile',
            verbose=1,
            layers=['dev', 'main'],
        ),
        id='layers-with-extra-after-layers',
    ),
    pytest.param(
        ['compile', '-v', '-vv', '-P', 'tox'], ['-P', 'tox'],
        Args(
            command='compile',
            verbose=3,
        ),
        id='no-layers-with-extra',
    ),
    pytest.param(
        ['compile', '-vvdfoo', '-P', 'tox'], ['-P', 'tox'],
        Args(
            command='compile',
            verbose=2,
            directory='foo',
        ),
        id='short-options-collapsed-with-extra',
    ),
    pytest.param(
        ['compile', '-q', '-y', 'dev', 'main', '-d', '/path'],
        ['-y', 'dev', 'main', '-d', '/path'],
        Args(
            command='compile',
            quiet=1,
        ),
        id='anything-after-extra-args-is-extra-arg',
    ),
    pytest.param(
        ['sync', '-c', 'path/to/config.toml', '-d', 'path/to/reqs'],
        [],
        Args(
            command='sync',
            config_path='path/to/config.toml',
            directory='path/to/reqs',
        ),
        id='config-path-and-directory',
    ),
    pytest.param(
        ['sync', '--no-config', '--tool=path/to/tool'],
        [],
        Args(
            command='sync',
            no_config=True,
            custom_tool='path/to/tool',
        ),
        id='no-config-and-custom-tool',
    ),
])
def test(
    args: List[str], expected_extra_args: List[str], expected_args: Args,
) -> None:
    set_defaults(expected_args)
    parser = build_parser()

    parsed_args, extra_args = parse_args(parser, args)

    assert vars(parsed_args) == vars(expected_args)
    assert extra_args == expected_extra_args


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    # we ignore this error, let's call it an expected behavior :)
    reason='fails on Python < 3.11 due to gh-60346',
)
@pytest.mark.parametrize(['args', 'expected_extra_args', 'expected_args'], [
    pytest.param(
        # since -vxyz contains options not supported by our parser, all the
        # collapsed opions are passed to the tool as is, thus no verbosity on
        # our side
        ['compile', '-vxyz', '-P', 'tox'], ['-vxyz', '-P', 'tox'],
        Args(command='compile'),
        id='collapsed-short-options-ignored-if-any-is-not-supported',
    ),
])
def test_py311_and_newer(
    args: List[str], expected_extra_args: List[str], expected_args: Args,
) -> None:
    set_defaults(expected_args)
    parser = build_parser()

    parsed_args, extra_args = parse_args(parser, args)

    assert vars(parsed_args) == vars(expected_args)
    assert extra_args == expected_extra_args
