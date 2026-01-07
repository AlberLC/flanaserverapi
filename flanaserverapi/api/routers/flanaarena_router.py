from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from api.dependencies.files import ensure_file_exists
from config import config

router = APIRouter(prefix='/flanaarena', tags=['flanaarena'])


@router.get('/download')
async def download(file_path: Annotated[Path, Depends(ensure_file_exists(config.flanaarena_zip_path))]) -> FileResponse:
    return FileResponse(file_path, filename=config.flanaarena_zip_name)
