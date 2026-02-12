from pathlib import Path

from fastapi import HTTPException, status

from config import config


def get_file_path(file_name: str) -> Path:
    file_path = config.files_path / file_name

    if not file_path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, config.file_not_found_message_error)

    return file_path
