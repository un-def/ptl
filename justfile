set positional-arguments


src_dir := 'src'
_pythonpath := env('PYTHONPATH', '')
export PYTHONPATH := if _pythonpath == '' { src_dir } else { src_dir + ':' + _pythonpath }


@_list:
  just --list

fix:
  isort .

lint:
  ruff check
  isort . -c

@test *args:
  pytest "${@}"

@tox *args:
  tox run "${@}"

@run *args:
  python -m ptl "${@}"
