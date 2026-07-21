from fastapi import Request
from fastapi.datastructures import URL

from config import config
from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository
from exceptions import NotVideoFileError
from utils import files


async def generate_html(
    file_id: str,
    file_url: URL,
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository,
    request: Request
) -> str:
    if (
        not (virtual_file := await virtual_file_repository.get_by_id(file_id))
        or
        not virtual_file.physical_file_id
        or
        not (physical_file := await physical_file_repository.get_by_id(virtual_file.physical_file_id))
    ):
        raise FileNotFoundError(config.file_not_found_error_message)

    mime_type = files.get_mime_type(virtual_file.name)
    main_type = mime_type.split('/')[0]
    og_type = config.open_graph_type_map.get(main_type, 'website')

    match main_type:
        case 'video':
            thumbnail_url = request.url_for('get_thumbnail', file_id=file_id)
        case 'image':
            thumbnail_url = file_url
        case 'audio':
            thumbnail_url = request.url_for(
                config.static_path.name,
                path=config.static_audio_thumbnail_path.relative_to(config.static_path).as_posix()
            )
        case _:
            thumbnail_url = request.url_for(
                config.static_path.name,
                path=config.static_default_thumbnail_path.relative_to(config.static_path).as_posix()
            )

    meta_tags_parts = [
        f'<title>{virtual_file.name}</title>',
        f'<meta property="og:title" content="{virtual_file.name}" />',
        f'<meta property="og:description" content="File: {virtual_file.name}" />',
        f'<meta property="og:type" content="{og_type}" />',
        f'<meta property="og:url" content="{file_url}" />',
        f'<meta property="og:image" content="{thumbnail_url}" />'
    ]

    if main_type == 'video':
        width, height = files.get_video_resolution(config.physical_files_path / str(physical_file.mongo_id))
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
        f'<h1>{virtual_file.name}</h1>',
        f'<p>Enlace directo: <a href="{file_url}">{file_url}</a></p>'
    ]

    match main_type:
        case 'video':
            body_parts.append(f'<video controls><source src="{file_url}" type="{mime_type}"></video>')
        case 'audio':
            body_parts.append(f'<audio controls><source src="{file_url}" type="{mime_type}"></audio>')
        case 'image':
            body_parts.append(f'<img src="{file_url}" alt="{virtual_file.name}" style="max-width:100%; height:auto;">')

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


async def get_video_thumbnail(
    file_id: str,
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> bytes:
    if (
        not (virtual_file := await virtual_file_repository.get_by_id(file_id))
        or
        not virtual_file.physical_file_id
        or
        not (physical_file := await physical_file_repository.get_by_id(virtual_file.physical_file_id))
    ):
        raise FileNotFoundError(config.file_not_found_error_message)

    mime_type = files.get_mime_type(virtual_file.name)
    if mime_type.split('/')[0] != 'video':
        raise NotVideoFileError

    return files.get_video_thumbnail(config.physical_files_path / str(physical_file.mongo_id))
