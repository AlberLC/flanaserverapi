from typing import Annotated

from fastapi import Depends, HTTPException, status

from api.dependencies.common_dependencies import get_root_path
from api.schemas.app import App
from config import config
from database.repositories.app_repository import AppRepository


async def get_app_exists(root_path: Annotated[str, Depends(get_root_path)]) -> App:
    if not (app := await AppRepository().get_by_id(root_path)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=config.document_not_found_message_error)

    return app
