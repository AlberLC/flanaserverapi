from fastapi import APIRouter
from fastapi.responses import FileResponse

from config import config

router = APIRouter(prefix='/flanacs', tags=['flanacs'])


@router.get('/download')
async def download() -> FileResponse:
    return FileResponse(config.flanacs_zip_path, filename=config.flanacs_zip_name)
