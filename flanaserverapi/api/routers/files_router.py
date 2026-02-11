from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, UploadFile, status

from api.schemas.file_info import FileInfo
from services import file_service

router = APIRouter(prefix='/files', tags=['files'])


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
async def delete_file(file_name: str) -> None:
    try:
        await file_service.delete_file(file_name)
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
