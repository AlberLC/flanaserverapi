import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response

from api import responses
from api.routers import uploads_router
from config import config
from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository
from enums import Environment
from services import file_service

router = APIRouter(prefix='/files', tags=['files'])
router.include_router(uploads_router.router)


@router.get('/{file_id}', response_model=None, response_class=Response, responses=responses.bytes_responses)
async def get_file(
    file_id: str,
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(PhysicalFileRepository)],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(VirtualFileRepository)]
) -> FileResponse | Response:
    try:
        physical_file, virtual_file = await file_service.get_file(
            file_id,
            physical_file_repository,
            virtual_file_repository
        )
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))

    physical_file_name = str(physical_file.mongo_id)

    if config.environment is Environment.DEVELOPMENT:
        return FileResponse(
            config.physical_files_path / physical_file_name,
            media_type=physical_file.mime_type,
            filename=virtual_file.name,
            content_disposition_type='inline'
        )
    else:
        return Response(
            headers={
                'Content-Type': physical_file.mime_type,
                'Content-Disposition': f"inline; filename*=utf-8''{urllib.parse.quote(virtual_file.name)}",
                'X-Accel-Redirect': f'/internal/files/{urllib.parse.quote(physical_file_name)}'
            }
        )


@router.delete('/{file_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(PhysicalFileRepository)],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(VirtualFileRepository)]
) -> None:
    try:
        await file_service.delete_file(file_id, physical_file_repository, virtual_file_repository)
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
