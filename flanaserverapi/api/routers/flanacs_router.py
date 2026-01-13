from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, PlainTextResponse

from api.dependencies.app_dependencies import get_app_exists
from api.dependencies.file_dependencies import get_file_path
from api.schemas.app import App
from config import config

router = APIRouter(prefix='/flanacs', tags=['flanacs'])


@router.get('/download')
async def download(file_path: Annotated[Path, Depends(get_file_path(config.flanacs_zip_path))]) -> FileResponse:
    return FileResponse(file_path, filename=config.flanacs_zip_name)


@router.get('/download/old')
async def download_old(file_path: Annotated[Path, Depends(get_file_path(config.flanacs_zip_path_old))]) -> FileResponse:
    return FileResponse(file_path, filename=config.flanacs_zip_name)


@router.get('/version')
async def get_version(app: Annotated[App, Depends(get_app_exists)]) -> PlainTextResponse:
    return PlainTextResponse(app['version'])
