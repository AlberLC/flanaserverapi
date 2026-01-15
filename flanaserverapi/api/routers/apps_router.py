from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, PlainTextResponse

from api.dependencies.app_dependencies import get_app, get_app_zip_path
from api.schemas.app import App

router = APIRouter(tags=['apps'])


@router.get('/{app_id}/download')
@router.get('/{app_id}/download/{release_type}')
async def download(zip_path: Annotated[Path, Depends(get_app_zip_path)]) -> FileResponse:
    return FileResponse(zip_path, filename=zip_path.name)


@router.get('/{app_id}/version')
async def get_version(app: Annotated[App, Depends(get_app)]) -> PlainTextResponse:
    return PlainTextResponse(app['version'])
