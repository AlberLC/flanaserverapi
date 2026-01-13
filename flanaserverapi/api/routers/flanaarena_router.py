from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from api.dependencies.file_dependencies import get_file_path
from config import config

router = APIRouter(prefix='/flanaarena', tags=['flanaarena'])


@router.get('/download')
async def download(file_path: Annotated[Path, Depends(get_file_path(config.flanaarena_zip_path))]) -> FileResponse:
    return FileResponse(file_path, filename=config.flanaarena_zip_name)
