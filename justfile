set positional-arguments


src_dir := 'src'
_pythonpath := env('PYTHONPATH', '')
export PYTHONPATH := if _pythonpath == '' { src_dir } else { src_dir + ':' + _pythonpath }


@_list:
  just --list --unsorted

fix:
  isort .

lint:
  ruff check
  isort . -c

type:
  mypy
  pyright

@test *args:
  pytest "${@}"

cov:
  #!/bin/sh -eu
  coverage erase
  tox run -q --skip-env '^(?!py\d{2,3}$)' -- -q --cov --cov-append --cov-report=
  coverage report -m

@tox *args:
  tox run "${@}"

@run *args:
  python -m ptl "${@}"

_ensure-uv:
  #!/bin/sh -eu
  cd requirements
  installed=$(pip freeze | grep -E '^uv==') || true
  required=$(grep -Eo '^uv==.[0-9a-z.]+' dev.requirements.in) || exit 127
  test "${installed}" = "${required}" || pip install "${required}"

@sync *args: _ensure-uv
  just run sync "${@}"

@compile *args: _ensure-uv
  just run compile "${@}"

@build:
  rm -rf build
  python -m build
