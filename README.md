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
    usage: ptl compile [--pip-tools | --uv | --tool TOOL] [-d DIR] [-v | -q] [-h]

    tool selection:
      --pip-tools           use `pip-compile`
      --uv                  use `uv pip compile`
      --tool TOOL           use custom tool

    compile options:
      -d DIR, --directory DIR
                            input directory
      -v, --verbose         get more output
      -q, --quiet           get less output
    ```

    By default, ptl checks for pip-tools and uv, and if both are installed, it conservatively prefers pip-tools. With `--pip-tools`/`--uv`/`--tool TOOL` you can explicitly choose the tool to use or provide your own tool.

    Any extra arguments are passed to the underlying tool.

    As part of the compile process, ptl generates temporary intermediate input files next to the original input files. Normally they are deleted at the end of the operation, but it's a good practice to add `*.ptl.in` (or `*.ptl.requirements.in` if you use the `<layer>.requirements.in` filename format) in your `.gitignore` anyway.

5. Run `ptl sync`:

    ```
    usage: ptl sync [--pip-tools | --uv | --tool TOOL] [-d DIR] [-v | -q] [-h]

    tool selection:
      --pip-tools           use `pip-sync`
      --uv                  use `uv pip sync`
      --tool TOOL           use custom tool

    sync options:
      -d DIR, --directory DIR
                            input directory
      -v, --verbose         get more output
      -q, --quiet           get less output
    ```

    As with `ptl compile`, any extra arguments are passed to the sync tool.

## Planned Features

* [x] Ability to compile/sync only some of the files ([0.2.0](https://github.com/un-def/ptl/releases/tag/0.2.0))
* [ ] Configuration via the config file and/or the enviroment variables.
