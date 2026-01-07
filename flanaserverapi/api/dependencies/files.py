from pathlib import Path
from typing import Callable

from fastapi import HTTPException, status

from config import config


def ensure_file_exists(path: str | Path) -> Callable[[], Path]:
    path = Path(path)

    def dependency() -> Path:
        if not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=config.file_not_found_message_error)

        return path

    return dependency
