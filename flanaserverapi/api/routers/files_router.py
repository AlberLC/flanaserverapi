from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile, status
from fastapi.responses import FileResponse

from api import responses
from api.dependencies.file_dependencies import get_file_path
from api.schemas.file_info import FileInfo
from services import file_service

router = APIRouter(prefix='/files', tags=['files'])


@router.get('/{file_name}', response_class=FileResponse, responses=responses.bytes_responses)
async def get_file(file_path: Annotated[Path, Depends(get_file_path)]) -> FileResponse:
    return FileResponse(file_path, filename=file_path.name, content_disposition_type='inline')


@router.post('', status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    expires_in: Annotated[
        int | None,
        Form(description='Time in seconds before the file is automatically deleted', ge=0)
    ] = None
) -> FileInfo:
    return await file_service.save_file(file, expires_in)


@router.delete('/{file_name}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_path: Annotated[Path, Depends(get_file_path)]) -> None:
    await file_service.delete_file(file_path)
