import mimetypes

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from exceptions import NotVideoFileError, ThumbnailError
from services import embed_service

router = APIRouter(prefix='/embeds', tags=['embeds'])


@router.get('/{file_name}')
async def embed_page(file_name: str, request: Request) -> Response:
    file_url = request.url_for('files', path=file_name)

    if 'bot' not in request.headers.get('user-agent', '').lower():
        return RedirectResponse(file_url)

    return HTMLResponse(content=embed_service.generate_html(file_name, file_url, request))


@router.get('/thumbnail/{file_name}')
async def thumbnail(file_name: str):
    try:
        return HTMLResponse(
            content=embed_service.get_video_thumbnail(file_name),
            media_type=mimetypes.types_map['.png']
        )
    except NotVideoFileError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ThumbnailError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
