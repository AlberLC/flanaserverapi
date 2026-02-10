from fastapi import Request
from fastapi.datastructures import URL

from config import config
from exceptions import NotVideoFileError
from utils import files


def generate_html(file_name: str, file_url: URL, request: Request) -> str:
    mime_type, main_type = files.get_mime_type(file_name)
    og_type = config.open_graph_type_map.get(main_type, 'website')

    match main_type:
        case 'video':
            thumbnail_url = request.url_for('thumbnail', file_name=file_name)
        case 'image':
            thumbnail_url = file_url
        case 'audio':
            thumbnail_url = request.url_for(
                'files',
                path=config.static_audio_thumbnail_path.relative_to(config.files_path).as_posix()
            )
        case _:
            thumbnail_url = request.url_for(
                'files',
                path=config.static_default_thumbnail_path.relative_to(config.files_path).as_posix()
            )

    meta_tags_parts = [
        f'<title>{file_name}</title>',
        f'<meta property="og:title" content="{file_name}" />',
        f'<meta property="og:description" content="File: {file_name}" />',
        f'<meta property="og:type" content="{og_type}" />',
        f'<meta property="og:url" content="{file_url}" />',
        f'<meta property="og:image" content="{thumbnail_url}" />'
    ]

    if main_type == 'video':
        width, height = files.get_video_resolution(config.files_path / file_name)
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

    # This should not be visible to anyone, but some human user agents might contain the string 'bot' and might have skipped the initial redirect
    body_parts = [
        f'<h1>{file_name}</h1>',
        f'<p>Enlace directo: <a href="{file_url}">{file_url}</a></p>'
    ]

    match main_type:
        case 'video':
            body_parts.append(f'<video controls><source src="{file_url}" type="{mime_type}"></video>')
        case 'audio':
            body_parts.append(f'<audio controls><source src="{file_url}" type="{mime_type}"></audio>')
        case 'image':
            body_parts.append(f'<img src="{file_url}" alt="{file_name}" style="max-width:100%; height:auto;">')

    meta_tags_content = '\n'.join(meta_tags_parts)
    body_content = '\n'.join(body_parts)

    return f'''
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


def get_video_thumbnail(file_name: str) -> bytes:
    file_path = config.files_path / file_name

    _, main_type = files.get_mime_type(file_name)

    if main_type != 'video':
        raise NotVideoFileError

    return files.get_video_thumbnail(file_path)
