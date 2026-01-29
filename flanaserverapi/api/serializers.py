from collections.abc import Iterable
from pathlib import Path


def to_raw_paths(paths: Iterable[Path]) -> list[str]:
    return [path.as_posix() for path in paths]
