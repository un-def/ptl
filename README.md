# ptl: pip-tools, layered

[![PyPI - Version](https://img.shields.io/pypi/v/ptl)](https://pypi.org/project/ptl/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ptl)](https://pypi.org/project/ptl/)
[![GitHub License](https://img.shields.io/github/license/un-def/ptl)](https://github.com/un-def/ptl/blob/master/LICENSE)

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/un-def/ptl/test.yml)](https://github.com/un-def/ptl/actions/workflows/test.yml)
[![Codecov](https://img.shields.io/codecov/c/github/un-def/ptl)](https://app.codecov.io/gh/un-def/ptl)

## Description

ptl is a [pip-tools](https://pip-tools.readthedocs.io/) wrapper for [multi-layered requirements](https://pip-tools.readthedocs.io/en/stable/#workflow-for-layered-requirements). There is already a project with the similar goal — [pip-compile-multi](https://pip-compile-multi.readthedocs.io) — but ptl has some key differences:

* It is much, much simpler. All it does is find requirements input files (`*.in`), generate intermediate input files with all references include transitive ones, and call `pip-compile` in topological order.
* It is supposed to be unopinionated — it doesn't have any options applied to the `pip-compile` command by default. Configure pip-tools as you wish.
* It has no dependencies, including pip-tools. Bring your own tools.
* It supports not only pip-tools, but also [uv](https://github.com/astral-sh/uv), or any other compatible tool.
* It has `pip-sync` functionality as well.

## Usage

1. Install ptl:

    ```
    pip install ptl
    ```

2. Install pip-tools or uv:

    ```
    pip install pip-tools
    ```

    or

    ```
    pip install uv
    ```

3. Prepare input files. By default, ptl looks for input files in the `requirements` directory and the current working directory. `<layer>.in` and `<layer>.requirements.in` filename formats are supported (although the latter may seem unnecessarily verbose, it's better suited for syntax highlighting rules — basically, any `*.requirements.{in,txt}` file as a “pip requirements” file). You can check out [the `requirements` directory of the ptl repository](https://github.com/un-def/ptl/tree/master/requirements) for an example (yes, we [eat our own dog food](https://en.wikipedia.org/wiki/Eating_your_own_dog_food)).

4. Run `ptl compile`:

    ```
    usage: ptl compile [-v | -q] [--pip-tools | --uv | --tool TOOL] [-d DIR] [--only] [LAYERS ...] [COMPILE OPTIONS ...]

    logging options:
      -v, --verbose         get more output
      -q, --quiet           get less output

    tool selection:
      --pip-tools           use `pip-compile`
      --uv                  use `uv pip compile`
      --tool TOOL           use custom tool

    compile options:
      -d DIR, --directory DIR
                            input directory
      LAYERS                layers to compile
      --only                compile only specified layers, not parent layers
    ```

    By default, ptl checks for pip-tools and uv, and if both are installed, it conservatively prefers pip-tools. With `--pip-tools`/`--uv`/`--tool TOOL` you can explicitly choose the tool to use or provide your own tool.

    Any extra arguments are passed to the underlying tool.

    As part of the compile process, ptl generates temporary intermediate input files next to the original input files. Normally they are deleted at the end of the operation, but it's a good practice to add `*.ptl.in` (or `*.ptl.requirements.in` if you use the `<layer>.requirements.in` filename format) in your `.gitignore` anyway.

5. Run `ptl sync`:

    ```
    usage: ptl sync [-v | -q] [--pip-tools | --uv | --tool TOOL] [-d DIR] [--only] [LAYERS ...] [SYNC OPTIONS ...]

    logging options:
      -v, --verbose         get more output
      -q, --quiet           get less output

    tool selection:
      --pip-tools           use `pip-sync`
      --uv                  use `uv pip sync`
      --tool TOOL           use custom tool

    sync options:
      -d DIR, --directory DIR
                            input directory
      LAYERS                layers to sync
      --only                sync only specified layers, not parent layers
    ```

    As with `ptl compile`, any extra arguments are passed to the sync tool.

## Configuration

ptl can be configured via 3 mechanisms, from highest to lowest precedence:

* command line options
* environment variables
* configuration files

### Configuration Files

ptl uses [TOML](https://toml.io/) format for its configuration file. Starting from Python 3.11, a TOML parser is included in the standard library (the `tomllib` module). In order to use configuration files with older Python versions, install the [tomli](https://github.com/hukkin/tomli) library, either manually:

```
pip install tomli
```

or as the `toml` “extra”:

```
pip install 'ptl[toml]'
```

It's safe to always install the `toml` “extra” since it installs `tomli` only for older Python versions.

If you don't need configuration files support, you can disable this feature with the `--no-config` command line flag or the `PTL_NO_CONFIG_FILE=1` environment variable, especially if you use older Python versions without tomli installed and have the `pyproject.toml` file in the project directory, since ptl will fail with the `ConfigError: no toml parser found` error in this case.

#### Configuration File Location

By default, ptl searches for a configuration file in the current working directory in the following order:

* `.ptl.toml`
* `ptl.toml`
* `pyproject.toml`

The first file found is used as a configuration file, even if it does not contain ptl configuration table. ptl does not merge configuration settings from several configuration files.

A location of the configuration file can be specified with the `-c PATH`/`--config=PATH` command line option or the `PTL_CONFIG_FILE=PATH` environment variable.

#### Configuration File Structure

All configuration settings are stored within the `[tool.ptl]` table. Settings specific to `sync`/`compile` commands are stored within corresponding `[tool.ptl.sync]`/`[tool.ptl.compile]` subtables. All settings are optional.

#### Configuration File Example

The following configuration contains all supported settings.

```toml
[tool.ptl]
directory = "deps"
verbosity = 1
tool = ":pip-tools:"

[tool.ptl.compile]
tool = ":uv:"
tool-options = "-U --no-build"

[tool.ptl.sync]
tool = "scripts/dep-sync.sh"
tool-options = "--ask"
```

### Configuration Settings

For each setting, its sources are listed in the following order:

* command line argument(s)
* enviroment variable(s)
* configuration file setting(s)

#### Directory

* `-d`/`--directory`
* `PTL_DIRECTORY`
* `tool.ptl.directory`

A directory where input files and generated lock files are stored. By default, ptl uses the `requirements` directory if it exists, otherwise the current working directory.

#### Verbosity

* `-v`/`--verbose`/`-q`/`--quiet`
* `PTL_VERBOSITY`
* `tool.ptl.verbosity`

A level of verbosity. The default value is 0, each `-v`/`--verbose` adds 1, each `-q`/`--quiet` subtracts 1. `PTL_VERBOSITY`/`tool.ptl.verbosity` are only used if there is no any verbosity argument in the command line, otherwise they are ignored.

#### Compile Tool

* `--pip-tools`/`--uv`/`--tool`
* `PTL_COMPILE_TOOL`/`PTL_TOOL`
* `too.ptl.compile.tool`/`tool.ptl.tool`

A tool used for the `compile` command. By default, ptl searches for pip-tools, then uv.

For `pip-compile` from `pip-tools` use one of:

* `ptl compile --pip-tools`
* `PTL_COMPILE_TOOL=:pip-tools:` or `PTL_TOOL=:pip-tools:`
* `tool = ":pip-tools:"` in the `[tool.ptl.compile]` or `[tool.ptl]` table

For `uv pip compile` use one of:

* `ptl compile --uv`
* `PTL_COMPILE_TOOL=:uv:` or `PTL_TOOL=:uv:`
* `tool = ":uv:"` in the `[tool.ptl.compile]` or `[tool.ptl]` table

For some custom tool use one of:

* `ptl compile --tool=scripts/custom.sh`
* `PTL_COMPILE_TOOL=scripts/custom.sh` or `PTL_TOOL=scripts/custom.sh`
* `tool = "scripts/custom.sh"` in the `[tool.ptl.compile]` or `[tool.ptl]` table

The order of precedence, from highest to lowest:

* the command line options
* the `PIP_COMPILE_TOOL` variable
* the `tool` setting in the `[tool.ptl.compile]` table
* the `PIP_TOOL` variable
* the `tool` setting in the `[tool.ptl]` table

#### Compile Tool Options

* any extra arguments not handled by ptl itself
* `PTL_COMPILE_TOOL_OPTIONS`
* `too.ptl.compile.tool-options`

Command line arguments passed to the compile tool. `PTL_COMPILE_TOOL_OPTIONS`/`too.ptl.compile.tool-options` are only used if there is no any extra arguments in the command line, otherwise they are ignored (not concatenated).

#### Sync Tool

* `--pip-tools`/`--uv`/`--tool`
* `PTL_SYNC_TOOL`/`PTL_TOOL`
* `too.ptl.sync.tool`/`tool.ptl.tool`

Same as **Compile Tool**, but for the `sync` command.

#### Sync Tool Options

* any extra arguments not handled by ptl itself
* `PTL_SYNC_TOOL_OPTIONS`
* `too.ptl.sync.tool-options`

Same as **Compile Tool Options**, but for the `sync` command.

## Planned Features

* [x] Ability to compile/sync only some of the files ([0.2.0](https://github.com/un-def/ptl/releases/tag/0.2.0))
* [x] Configuration via the config file and/or the enviroment variables ([0.3.0](https://github.com/un-def/ptl/releases/tag/0.3.0))
