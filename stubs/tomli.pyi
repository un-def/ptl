from typing import IO, Any, Callable


def load(   # type: ignore[misc] # noqa: E303
    __fp: IO[bytes], *, parse_float: Callable[[str], Any] = float,
) -> dict[str, Any]:
    ...
