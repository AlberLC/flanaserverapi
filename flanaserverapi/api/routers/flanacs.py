from fastapi import APIRouter
from fastapi.responses import FileResponse

from config import config

router = APIRouter(prefix='/flanacs', tags=['flanacs'])


@router.get('/download')
async def download() -> FileResponse:
    return FileResponse(config.flanacs_zip_path, filename=config.flanacs_zip_name)


@router.get('/download/old')
async def download_old() -> FileResponse:
    return FileResponse(config.flanacs_zip_path_old, filename=config.flanacs_zip_name)
