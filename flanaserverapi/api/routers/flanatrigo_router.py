from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, PlainTextResponse

from api.dependencies.files import ensure_file_exists
from config import config

router = APIRouter(prefix='/flanatrigo', tags=['flanatrigo'])


@router.get('/download')
async def download(file_path: Annotated[Path, Depends(ensure_file_exists(config.flanatrigo_zip_path))]) -> FileResponse:
    return FileResponse(file_path, filename=config.flanatrigo_zip_name)


@router.get('/version')
async def get_version(
    file_path: Annotated[Path, Depends(ensure_file_exists(config.flanatrigo_version_path))]
) -> PlainTextResponse:
    return PlainTextResponse(file_path.read_text().strip())
