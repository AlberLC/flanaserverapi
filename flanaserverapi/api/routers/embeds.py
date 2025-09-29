from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

import utils
from config import config

router = APIRouter(prefix='/embeds', tags=['embeds'])


@router.get('/{file_name}')
async def embed_page(file_name: str, request: Request) -> HTMLResponse:
    file_url = request.url_for('files', path=file_name)

    mime_type, main_type = utils.get_mime_type(file_name)
    og_type = config.open_graph_type_map.get(main_type, 'website')

    match main_type:
        case 'video':
            thumbnail_url = request.url_for('thumbnail', file_name=file_name)
        case 'image':
            thumbnail_url = file_url
        case 'audio':
            thumbnail_url = request.url_for('files', path=config.audio_thumbnail_name)
        case _:
            thumbnail_url = request.url_for('files', path=config.default_thumbnail_name)

    meta_tags_parts = [
        f'<title>{file_name}</title>',
        f'<meta property="og:title" content="{file_name}" />',
        f'<meta property="og:description" content="File: {file_name}" />',
        f'<meta property="og:type" content="{og_type}" />',
        f'<meta property="og:url" content="{file_url}" />',
        f'<meta property="og:image" content="{thumbnail_url}" />'
    ]

    if main_type == 'video':
        width, height = utils.get_video_resolution(config.files_path / file_name)
        meta_tags_parts.extend(
            (
                f'<meta property="og:video" content="{file_url}" />',
                f'<meta property="og:video:type" content="{mime_type}" />',
                f'<meta property="og:video:width" content="{width}" />',
                f'<meta property="og:video:height" content="{height}" />'
            )
        )
    elif main_type == 'audio':
        meta_tags_parts.extend(
            (
                f'<meta property="og:audio" content="{file_url}" />',
                f'<meta property="og:audio:type" content="{mime_type}" />'
            )
        )

    body_parts = [
        f'<h1>{file_name}</h1>',
        f'<p>Enlace directo: <a href="{file_url}">{file_url}</a></p>'
    ]

    match main_type:
        case 'video':
            body_parts.append(f"<video controls><source src='{file_url}' type='{mime_type}'></video>")
        case 'audio':
            body_parts.append(f"<audio controls><source src='{file_url}' type='{mime_type}'></audio>")
        case 'image':
            body_parts.append(f"<img src='{file_url}' alt='{file_name}' style='max-width:100%; height:auto;'>")

    meta_tags_content = '\n'.join(meta_tags_parts)
    body_content = '\n'.join(body_parts)

    html_content = f'''
        <!DOCTYPE html>
        <html lang='es'>
        <head>
        {meta_tags_content}
        </head>
        <body>
        {body_content}
        </body>
        </html>
    '''

    return HTMLResponse(content=html_content)


@router.get('/thumbnail/{file_name}')
async def thumbnail(file_name: str):
    file_path = config.files_path / file_name

    _, main_type = utils.get_mime_type(file_name)

    if main_type != 'video':
        raise HTTPException(status_code=400, detail='Thumbnail only available for videos')

    try:
        thumbnail_bytes = utils.get_video_thumbnail(file_path, config.thumbnail_second)
    except RuntimeError:
        raise HTTPException(status_code=500, detail='Error generating thumbnail')

    return HTMLResponse(content=thumbnail_bytes, media_type='image/png')
