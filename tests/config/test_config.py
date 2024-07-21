from pathlib import Path
from typing import Dict, List, Optional, Union

import pytest

from ptl.config import Config
from ptl.exceptions import ConfigError
from ptl.providers import Provider, Tool

from tests.testlib import dedent


# pyright: reportPrivateUsage=false


class TestSuiteBase:
    environ: Dict[str, str]

    @pytest.fixture(autouse=True)
    def base_setup(
        self, monkeypatch: pytest.MonkeyPatch, tmp_cwd: Path,
    ) -> None:
        self.cwd = tmp_cwd
        self.environ = {}
        monkeypatch.setattr(Config, '_environ', self.environ)

    def set_env(self, key: str, value: str) -> None:
        self.environ[key] = value

    def write_config(self, path: Union[Path, str], content: str) -> Path:
        path = self.cwd / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(content))
        return path

    def create_config(self, content: str) -> Path:
        return self.write_config('ptl.toml', content)


class LoadConfigTestSuite(TestSuiteBase):

    def test_path_from_args(self) -> None:
        self.set_env('PTL_CONFIG_FILE', 'ignored')
        config_path = self.write_config('conf/file.toml', """
            [tool.ptl]
            directory = "reqs"
        """)

        config = Config('conf/file.toml')

        assert config._config_path == config_path
        assert config._config_dict == {'directory': 'reqs'}

    def test_path_from_env(self) -> None:
        self.set_env('PTL_CONFIG_FILE', 'conf/env.toml')
        config_path = self.write_config('conf/env.toml', """
            [tool.ptl]
            directory = "reqs"
        """)

        config = Config()

        assert config._config_path == config_path
        assert config._config_dict == {'directory': 'reqs'}

    def test_ignore_config_file_true_from_args(self) -> None:
        self.set_env('PTL_NO_CONFIG_FILE', 'false')   # should be ignored
        self.write_config('conf/file.toml', """
            [tool.ptl]
            directory = "reqs"
        """)

        config = Config('conf/file.toml', ignore_config_file=True)

        assert config._config_path is None
        assert config._config_dict == {}

    def test_ignore_config_file_false_from_args(self) -> None:
        self.set_env('PTL_NO_CONFIG_FILE', 'true')   # should be ignored
        config_path = self.write_config('conf/file.toml', """
            [tool.ptl]
            directory = "reqs"
        """)

        config = Config('conf/file.toml', ignore_config_file=False)

        assert config._config_path == config_path
        assert config._config_dict == {'directory': 'reqs'}

    def test_ignore_config_file_true_from_env(self) -> None:
        self.set_env('PTL_NO_CONFIG_FILE', 'true')
        self.write_config('conf/file.toml', """
            [tool.ptl]
            directory = "reqs"
        """)

        config = Config('conf/file.toml')

        assert config._config_path is None
        assert config._config_dict == {}

    def test_ignore_config_file_false_from_env(self) -> None:
        self.set_env('PTL_NO_CONFIG_FILE', 'false')
        config_path = self.write_config('conf/file.toml', """
            [tool.ptl]
            directory = "reqs"
        """)

        config = Config('conf/file.toml')

        assert config._config_path == config_path
        assert config._config_dict == {'directory': 'reqs'}

    def test_autodiscovery(self) -> None:
        config_path = self.write_config('pyproject.toml', """
            [tool.ptl]
            directory = "reqs"
        """)

        config = Config()

        assert config._config_path == config_path
        assert config._config_dict == {'directory': 'reqs'}

    def test_autodiscovery_config_not_found(self) -> None:
        config = Config()

        assert config._config_path is None
        assert config._config_dict == {}


class ValidationTestSuite(TestSuiteBase):

    def test_not_a_table(self) -> None:
        self.create_config("""
            [tool.ptl.foo]
            bar = 1
        """)

        with pytest.raises(
            ConfigError, match=r'foo\.bar must be a table, got int',
        ):
            Config()._get_file_value(str, 'foo.bar.baz')

    def test_env_type_int(self) -> None:
        self.set_env('PTL_INTVAR', 'foo')

        with pytest.raises(ConfigError, match='PTL_INTVAR: invalid literal'):
            Config()._get_env_value(int, 'INTVAR')

    def test_file_type_int(self) -> None:
        self.create_config("""
            [tool.ptl]
            intopt = "1"
        """)

        with pytest.raises(
            ConfigError, match=r'intopt: int expected, got str',
        ):
            Config()._get_file_value(int, 'intopt')

    @pytest.mark.parametrize(['value', 'expected'], [
        ('1', True), ('True', True), ('true', True),
        ('YES', True), ('on', True), ('On', True),
        ('0', False), ('FALSE', False), ('faLSE', False),
        ('no', False), ('NO', False), ('Off', False),
    ])
    def test_env_type_bool_ok(self, value: str, expected: bool) -> None:
        self.set_env('PTL_BOOLVAR', value)

        actual = Config()._get_env_value(bool, 'BOOLVAR')

        assert actual is expected

    @pytest.mark.parametrize('value', ['', '2', 'foo'])
    def test_env_type_bool_error(self, value: str) -> None:
        self.set_env('PTL_BOOLVAR', value)

        with pytest.raises(
            ConfigError, match=f"invalid bool value: '{value}'",
        ):
            Config()._get_env_value(bool, 'BOOLVAR')


class DirectoryTestSuite(TestSuiteBase):

    def test_env(self) -> None:
        self.set_env('PTL_DIRECTORY', 'reqs')
        self.create_config("""
            [tool.ptl]
            directory = "ignored"
        """)

        config = Config()

        assert config.directory == self.cwd / 'reqs'

    def test_file(self) -> None:
        self.create_config("""
            [tool.ptl]
            directory = "dir/reqs"
        """)

        config = Config()

        assert config.directory == self.cwd / 'dir/reqs'

    def test_default(self) -> None:
        config = Config()

        assert config.directory is None


class VerbosityTestSuite(TestSuiteBase):

    def test_env(self) -> None:
        self.set_env('PTL_VERBOSITY', '-1')
        self.create_config("""
            [tool.ptl]
            verbosity = 2
        """)

        config = Config()

        assert config.verbosity == -1

    def test_file(self) -> None:
        self.create_config("""
            [tool.ptl]
            verbosity = 1
        """)

        config = Config()

        assert config.verbosity == 1

    def test_default(self) -> None:
        config = Config()

        assert config.verbosity == 0


class GetToolTestSuite(TestSuiteBase):

    @pytest.mark.parametrize(
        [
            'global_env', 'compile_env', 'global_file', 'compile_file',
            'expected',
        ], [
            # default
            (None, None, None, None, None),
            # global file, uv
            (None, None, ':uv:', None, Provider.UV),
            # global file, custom
            (None, None, 'f -foo', None, 'f -foo'),
            # compile file, pip-tools
            (None, None, 'f -foo', ':pip-tools:', Provider.PIP_TOOLS),
            # compile file, custom
            (None, None, 'f -foo', 'f -bar', 'f -bar'),
            # global env, uv, global file ignored
            (':uv:', None, ':pip-tools:', None, Provider.UV),
            # global env, uv, compile file respected
            (':uv:', None, ':pip-tools:', 'f -foo', 'f -foo'),
            # compile env, custom, global file ignored
            ('e -foo', 'e -bar', ':uv:', None, 'e -bar'),
            # compile env, custom, compile file ignored
            ('e -foo', 'e -bar', ':uv:', ':pip-tools:', 'e -bar'),
        ],
    )
    def test_compile(
        self, global_env: Optional[str], compile_env: Optional[str],
        global_file: Optional[str], compile_file: Optional[str],
        expected: Optional[str],
    ) -> None:
        if global_env is not None:
            self.set_env('PTL_TOOL', global_env)
        if compile_env is not None:
            self.set_env('PTL_COMPILE_TOOL', compile_env)
        config_lines: List[str] = []
        if global_file is not None:
            config_lines.append('[tool.ptl]')
            config_lines.append(f'tool = "{global_file}"')
        if compile_file is not None:
            config_lines.append('[tool.ptl.compile]')
            config_lines.append(f'tool = "{compile_file}"')
        if config_lines:
            self.create_config('\n'.join(config_lines))

        config = Config()

        assert config.get_tool(Tool.COMPILE) == expected

    @pytest.mark.parametrize(
        [
            'global_env', 'sync_env', 'global_file', 'sync_file',
            'expected',
        ], [
            # default
            (None, None, None, None, None),
            # global file, pip-tools
            (None, None, ':pip-tools:', None, Provider.PIP_TOOLS),
            # global file, custom
            (None, None, 'f -foo', None, 'f -foo'),
            # sync file, uv
            (None, None, 'f -foo', ':uv:', Provider.UV),
            # sync file, custom
            (None, None, 'f -foo', 'f -bar', 'f -bar'),
            # global env, pip-tools, global file ignored
            (':pip-tools:', None, ':uv:', None, Provider.PIP_TOOLS),
            # global env, uv, sync file respected
            (':uv:', None, ':pip-tools:', 'f -foo', 'f -foo'),
            # sync env, custom, global file ignored
            ('e -foo', 'e -bar', ':pip-tools:', None, 'e -bar'),
            # compile env, custom, sync file ignored
            ('e -foo', 'e -bar', ':pip-tools:', ':pip-tools:', 'e -bar'),
        ],
    )
    def test_sync(
        self, global_env: Optional[str], sync_env: Optional[str],
        global_file: Optional[str], sync_file: Optional[str],
        expected: Optional[str],
    ) -> None:
        if global_env is not None:
            self.set_env('PTL_TOOL', global_env)
        if sync_env is not None:
            self.set_env('PTL_SYNC_TOOL', sync_env)
        config_lines: List[str] = []
        if global_file is not None:
            config_lines.append('[tool.ptl]')
            config_lines.append(f'tool = "{global_file}"')
        if sync_file is not None:
            config_lines.append('[tool.ptl.sync]')
            config_lines.append(f'tool = "{sync_file}"')
        if config_lines:
            self.create_config('\n'.join(config_lines))

        config = Config()

        assert config.get_tool(Tool.SYNC) == expected


class GetToolOptionsTestSuite(TestSuiteBase):

    @pytest.mark.parametrize(
        ['compile_tool_options_env', 'compile_tool_options_file', 'expected'],
        [
            # default
            (None, None, None),
            # empty string, env
            ('', None, []),
            # env
            ('-a -b', '-ignored', ['-a', '-b']),
            # file
            (None, '-c -d', ['-c', '-d']),
        ],
    )
    def test_compile(
        self, compile_tool_options_env: Optional[str],
        compile_tool_options_file: Optional[str],
        expected: List[str],
    ) -> None:
        if compile_tool_options_env is not None:
            self.set_env('PTL_COMPILE_TOOL_OPTIONS', compile_tool_options_env)
        config_lines: List[str] = []
        if compile_tool_options_file is not None:
            config_lines.append('[tool.ptl.compile]')
            config_lines.append(
                f'tool-options = "{compile_tool_options_file}"')
        self.create_config('\n'.join(config_lines))

        config = Config()

        assert config.get_tool_options(Tool.COMPILE) == expected

    @pytest.mark.parametrize(
        ['sync_tool_options_env', 'sync_tool_options_file', 'expected'],
        [
            # default
            (None, None, None),
            # empty string, file
            (None, '', []),
            # env
            ('-a -b', '-ignored', ['-a', '-b']),
            # file
            (None, '-c -d', ['-c', '-d']),
        ],
    )
    def test_sync(
        self, sync_tool_options_env: Optional[str],
        sync_tool_options_file: Optional[str],
        expected: Optional[List[str]],
    ) -> None:
        if sync_tool_options_env is not None:
            self.set_env('PTL_SYNC_TOOL_OPTIONS', sync_tool_options_env)
        config_lines: List[str] = []
        if sync_tool_options_file is not None:
            config_lines.append('[tool.ptl.sync]')
            config_lines.append(f'tool-options = "{sync_tool_options_file}"')
        self.create_config('\n'.join(config_lines))

        config = Config()

        assert config.get_tool_options(Tool.SYNC) == expected
