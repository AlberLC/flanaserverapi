import mimetypes
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository
from exceptions import NotVideoFileError, ThumbnailError
from services import embed_service

router = APIRouter(prefix='/embeds', tags=['embeds'])


@router.get('/{file_id}', response_model=None, response_class=Response)
async def get_embed_page(
    file_id: str,
    user_agent: Annotated[str, Header()],
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(PhysicalFileRepository)],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(VirtualFileRepository)],
    request: Request
) -> HTMLResponse | RedirectResponse:
    file_url = request.url_for('get_file', file_id=file_id)

    if 'bot' not in user_agent.lower():
        return RedirectResponse(file_url)

    try:
        return HTMLResponse(
            await embed_service.generate_html(
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
    '/thumbnail/{file_id}',
    response_class=Response,
    responses={status.HTTP_200_OK: {'content': {mimetypes.types_map['.png']: {}}}}
)
async def get_thumbnail(
    file_id: str,
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(PhysicalFileRepository)],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(VirtualFileRepository)]
) -> Response:
    try:
        return Response(
            await embed_service.get_video_thumbnail(file_id, physical_file_repository, virtual_file_repository),
            media_type=mimetypes.types_map['.png']
        )
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except NotVideoFileError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except ThumbnailError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
