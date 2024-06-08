set positional-arguments


@_list:
  just --list

lint:
  ruff check
  isort . -c

@run *args:
  PYTHONPATH=src python -m ptl "${@}"
