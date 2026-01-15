from pathlib import Path

from fastapi import HTTPException, status

from api.schemas.app import App
from config import config
from custom_types import AppId
from database.repositories.app_repository import AppRepository
from enums import ReleaseType


async def get_app(app_id: AppId) -> App:
    if not (app := await AppRepository().get_by_id(app_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=config.document_not_found_message_error)

    return app


def get_app_zip_path(app_id: AppId, release_type: ReleaseType | None = ReleaseType.LATEST) -> Path:
    file_name_suffix = '_old' if release_type is ReleaseType.OLD else ''
    path = config.apps_path / f'{config.app_names[app_id]}{file_name_suffix}.zip'

    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=config.file_not_found_message_error)

    return path
