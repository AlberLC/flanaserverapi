import mimetypes
import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response

from api import responses
from api.dependencies.http_dependencies import get_access_token_hash
from api.dependencies.repository_dependencies import get_repository
from api.routers import uploads_router
from api.schemas.files import File, Files
from config import config
from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository
from enums import Environment
from services import file_service

router = APIRouter(prefix='/files', tags=['files'])
router.include_router(uploads_router.router)


@router.get('')
async def get_files(
    access_token_hash: Annotated[str, Depends(get_access_token_hash)],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(get_repository(VirtualFileRepository))],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1)] = config.files_default_limit
    return await file_service.get_files(access_token_hash, virtual_file_repository, skip, limit)
) -> Files:


@router.get('/{file_id}')
async def get_file(
    file_id: str,
    access_token_hash: Annotated[str, Depends(get_access_token_hash)],
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(get_repository(PhysicalFileRepository))],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(get_repository(VirtualFileRepository))]
) -> File:
    try:
        return await file_service.get_file(
            file_id,
            access_token_hash,
            physical_file_repository,
            virtual_file_repository
        )
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get('/{file_id}/content', response_model=None, response_class=Response, responses=responses.bytes_responses)
async def get_file_content(
    file_id: str,
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(get_repository(PhysicalFileRepository))],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(get_repository(VirtualFileRepository))]
) -> FileResponse | Response:
    try:
        physical_file, virtual_file = await file_service.get_file_models(
            file_id,
            physical_file_repository,
            virtual_file_repository
        )
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))

    if config.environment is Environment.DEVELOPMENT:
        return FileResponse(
            file_service.build_physical_file_path(physical_file.mongo_id),
            media_type=physical_file.mime_type,
            filename=virtual_file.name,
            content_disposition_type='inline'
        )
    else:
        return Response(
            headers={
                'Content-Type': physical_file.mime_type,
                'Content-Disposition': f"inline; filename*=utf-8''{urllib.parse.quote(virtual_file.name)}",
                'X-Accel-Redirect': f'/internal/files/{physical_file.mongo_id}'
            }
        )


@router.get('/{file_id}/embed', response_model=None, response_class=Response)
async def get_file_embed_page(
    file_id: str,
    user_agent: Annotated[str, Header()],
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(get_repository(PhysicalFileRepository))],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(get_repository(VirtualFileRepository))],
    request: Request
) -> HTMLResponse | RedirectResponse:
    file_url = request.url_for('get_file_content', file_id=file_id)

    if 'bot' not in user_agent.lower():
        return RedirectResponse(file_url)

    try:
        return HTMLResponse(
            await file_service.generate_embed_page(
                file_id,
                file_url,
                physical_file_repository,
                virtual_file_repository,
                request
            )
        )
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get(
    '/{file_id}/thumbnail',
    response_class=FileResponse,
    responses={status.HTTP_200_OK: {'content': {mimetypes.types_map[config.thumbnails_extension]: {}}}}
)
async def get_file_thumbnail(
    file_id: str,
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(get_repository(PhysicalFileRepository))],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(get_repository(VirtualFileRepository))]
) -> FileResponse:
    try:
        return FileResponse(
            await file_service.get_file_thumbnail_path(file_id, physical_file_repository, virtual_file_repository),
            media_type=mimetypes.types_map[config.thumbnails_extension]
        )
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.delete('/{file_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    access_token_hash: Annotated[str, Depends(get_access_token_hash)],
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(get_repository(PhysicalFileRepository))],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(get_repository(VirtualFileRepository))]
) -> None:
    try:
        await file_service.delete_file(file_id, access_token_hash, physical_file_repository, virtual_file_repository)
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
