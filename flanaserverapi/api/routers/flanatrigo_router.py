from fastapi import APIRouter
from fastapi.responses import FileResponse, PlainTextResponse

from config import config

router = APIRouter(prefix='/flanatrigo', tags=['flanatrigo'])


@router.get('/download')
async def download() -> FileResponse:
    return FileResponse(config.flanatrigo_zip_path, filename=config.flanatrigo_zip_name)


@router.get('/version')
async def get_version() -> PlainTextResponse:
    return PlainTextResponse(config.flanatrigo_version_path.read_text().strip())
