from fastapi import APIRouter
from fastapi.responses import FileResponse

from config import config

router = APIRouter(prefix='/flanaarena', tags=['flanaarena'])


@router.get('/download')
async def download() -> FileResponse:
    return FileResponse(config.flanaarena_zip_path, filename=config.flanaarena_zip_name)
