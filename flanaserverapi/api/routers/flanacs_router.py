from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, PlainTextResponse

from api.dependencies.files import ensure_file_exists
from config import config

router = APIRouter(prefix='/flanacs', tags=['flanacs'])


@router.get('/download')
async def download(file_path: Annotated[Path, Depends(ensure_file_exists(config.flanacs_zip_path))]) -> FileResponse:
    return FileResponse(file_path, filename=config.flanacs_zip_name)


@router.get('/download/old')
async def download_old(
    file_path: Annotated[Path, Depends(ensure_file_exists(config.flanacs_zip_path_old))]
) -> FileResponse:
    return FileResponse(file_path, filename=config.flanacs_zip_name)


@router.get('/version')
async def get_version(
    file_path: Annotated[Path, Depends(ensure_file_exists(config.flanacs_version_path))]
) -> PlainTextResponse:
    return PlainTextResponse(file_path.read_text().strip())
