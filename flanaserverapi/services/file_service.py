import asyncio
import datetime
from collections import defaultdict
from collections.abc import AsyncGenerator, Sequence
from pathlib import Path

import pymongo
from bson import ObjectId
from fastapi import Request
from fastapi.datastructures import URL

from api.schemas.files import File, Files, PhysicalFile, TemporaryFile, VirtualFile
from config import config
from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.temporary_file_repository import TemporaryFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository
from database.transactions import mongo_transaction
from utils import file_utils


async def _clean_up_files(ids: set[str], files_path: Path) -> None:
    for file_path in files_path.iterdir():
        if file_path.is_file() and file_path.stem not in ids:
            await _delete_file(file_path)


async def _clean_up_physical_files(
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> None:
    physical_file_ids = {
        str(physical_file.mongo_id)
        async for physical_file in _iter_valid_physical_files(physical_file_repository, virtual_file_repository)
    }
    await _clean_up_files(physical_file_ids, config.physical_files_path)
    await _clean_up_files(physical_file_ids, config.thumbnails_path)


async def _clean_up_temporary_files(temporary_file_repository: TemporaryFileRepository) -> None:
    await _clean_up_files(
        {temporary_file.mongo_id async for temporary_file in _iter_valid_temporary_files(temporary_file_repository)},
        config.temporary_files_path
    )


async def _clean_up_virtual_files(
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> None:
    virtual_file_ids_to_delete = []

    async for virtual_file in virtual_file_repository.iter():
        if (
            virtual_file.physical_file_id
            and
            not await physical_file_repository.get_one({'_id': virtual_file.physical_file_id})
        ):
            virtual_file_ids_to_delete.append(virtual_file.mongo_id)

    await virtual_file_repository.delete({'_id': {'$in': virtual_file_ids_to_delete}})


async def _delete_file(file_path: Path) -> None:
    try:
        await asyncio.to_thread(file_path.unlink, missing_ok=True)
    except PermissionError:
        pass


async def _delete_physical_files(ids: Sequence[ObjectId], physical_file_repository: PhysicalFileRepository) -> None:
    for id in ids:
        await _delete_file(build_physical_file_path(id))
        await _delete_file(build_thumbnail_path(id))

    await physical_file_repository.delete({'_id': {'$in': ids}})


async def _delete_virtual_files(
    virtual_files: Sequence[VirtualFile],
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository,
    physical_files_by_id: dict[ObjectId, PhysicalFile] | None = None
) -> None:
    if physical_files_by_id is None:
        physical_file_ids = tuple(
            virtual_file.physical_file_id for virtual_file in virtual_files if virtual_file.physical_file_id
        )
        physical_files_by_id = {
            physical_file.mongo_id: physical_file
            async for physical_file in physical_file_repository.iter({'_id': {'$in': physical_file_ids}})
        }

    physical_file_ids_to_delete = []
    virtual_file_ids_to_delete = []
    referenced_virtual_file_ids_to_pull = defaultdict(list)

    for virtual_file in virtual_files:
        virtual_file_ids_to_delete.append(virtual_file.mongo_id)

        if virtual_file.physical_file_id:
            referenced_virtual_file_ids_to_pull[virtual_file.physical_file_id].append(virtual_file.mongo_id)

    for physical_file_id, virtual_file_ids in referenced_virtual_file_ids_to_pull.items():
        physical_file = physical_files_by_id[physical_file_id]

        if len(physical_file.virtual_file_ids) > len(virtual_file_ids):
            await physical_file_repository.partial_update_one(
                {'_id': physical_file_id}, {'$pull': {'virtual_file_ids': {'$in': virtual_file_ids}}}
            )
        else:
            physical_file_ids_to_delete.append(physical_file.mongo_id)

    await virtual_file_repository.delete({'_id': {'$in': virtual_file_ids_to_delete}})
    await _delete_physical_files(physical_file_ids_to_delete, physical_file_repository)


async def _get_used_storage(
    physical_file_repository: PhysicalFileRepository,
    temporary_file_repository: TemporaryFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> int:
    used_storage = 0

    async for physical_file in _iter_valid_physical_files(physical_file_repository, virtual_file_repository):
        used_storage += physical_file.size

    async for temporary_file in _iter_valid_temporary_files(temporary_file_repository):
        if not temporary_file.virtual_file_id:
            used_storage += temporary_file.size

    return used_storage


async def _iter_valid_physical_files(
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> AsyncGenerator[PhysicalFile]:
    now = datetime.datetime.now(datetime.UTC)
    physical_file_ids_to_delete = []
    physical_files_by_id = {}
    virtual_files_to_delete = []

    async for physical_file in physical_file_repository.iter():
        referenced_virtual_files = await virtual_file_repository.get(
            {'_id': {'$in': tuple(physical_file.virtual_file_ids)}}
        )

        if not build_physical_file_path(physical_file.mongo_id).is_file():
            virtual_files_to_delete.extend(referenced_virtual_files)
            physical_file_ids_to_delete.append(physical_file.mongo_id)
            physical_files_by_id[physical_file.mongo_id] = physical_file
            continue

        has_valid_reference = False

        for virtual_file in referenced_virtual_files:
            if virtual_file.expires_at and now >= virtual_file.expires_at:
                virtual_files_to_delete.append(virtual_file)
                physical_files_by_id[physical_file.mongo_id] = physical_file
            else:
                has_valid_reference = True

        if has_valid_reference:
            yield physical_file
        else:
            physical_file_ids_to_delete.append(physical_file.mongo_id)

    await _delete_virtual_files(
        virtual_files_to_delete,
        physical_file_repository,
        virtual_file_repository,
        physical_files_by_id
    )
    await _delete_physical_files(physical_file_ids_to_delete, physical_file_repository)


async def _iter_valid_temporary_files(
    temporary_file_repository: TemporaryFileRepository
) -> AsyncGenerator[TemporaryFile]:
    now = datetime.datetime.now(datetime.UTC)
    temporary_file_ids_to_delete = []

    async for temporary_file in temporary_file_repository.iter():
        if (
            now < temporary_file.created_at + config.temporary_files_ttl
            and
            (
                now < temporary_file.created_at + config.temporary_files_cleanup_protection_period
                or
                temporary_file.virtual_file_id
                or
                build_temporary_file_path(temporary_file.mongo_id).is_file()
            )
        ):
            yield temporary_file
        else:
            temporary_file_ids_to_delete.append(temporary_file.mongo_id)

    await delete_temporary_files(temporary_file_ids_to_delete, temporary_file_repository)


def build_physical_file_path(id: ObjectId) -> Path:
    return config.physical_files_path / str(id)


def build_temporary_file_path(id: str) -> Path:
    return config.temporary_files_path / id


def build_thumbnail_path(id: ObjectId) -> Path:
    return (config.thumbnails_path / str(id)).with_suffix(config.thumbnails_extension)


async def clean_up_files(
    physical_file_repository: PhysicalFileRepository,
    temporary_file_repository: TemporaryFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> None:
    await _clean_up_physical_files(physical_file_repository, virtual_file_repository)
    await _clean_up_temporary_files(temporary_file_repository)
    await _clean_up_virtual_files(physical_file_repository, virtual_file_repository)


def create_file(physical_file: PhysicalFile, virtual_file: VirtualFile) -> File:
    return File(
        id=virtual_file.mongo_id,
        name=virtual_file.name,
        url=f'/files/{virtual_file.mongo_id}/content',
        embed_url=f'/files/{virtual_file.mongo_id}/embed',
        thumbnail_url=f'/files/{virtual_file.mongo_id}/thumbnail',
        created_at=virtual_file.created_at,
        expires_at=virtual_file.expires_at
    )


async def delete_file(
    file_id: str,
    access_token_hash: str,
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> None:
    if not (
        virtual_file := await virtual_file_repository.get_one({'_id': file_id, 'access_token_hash': access_token_hash})
    ):
        raise FileNotFoundError(config.file_not_found_error_message)

    await _delete_virtual_files((virtual_file,), physical_file_repository, virtual_file_repository)


async def delete_temporary_files(ids: Sequence[str], temporary_file_repository: TemporaryFileRepository) -> None:
    for id in ids:
        await _delete_file(build_temporary_file_path(id))

    await temporary_file_repository.delete({'_id': {'$in': ids}})


@mongo_transaction
async def enforce_storage_limit(
    physical_file_repository: PhysicalFileRepository,
    temporary_file_repository: TemporaryFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> None:
    used_storage = await _get_used_storage(physical_file_repository, temporary_file_repository, virtual_file_repository)

    if used_storage <= config.files_max_storage_size:
        return

    physical_files_to_delete_by_id = {}
    virtual_file_ids_to_delete = []

    async for physical_file in physical_file_repository.iter(sort_keys=('created_at',)):
        virtual_file_ids_to_delete.extend(physical_file.virtual_file_ids)
        physical_files_to_delete_by_id[physical_file.mongo_id] = physical_file
        used_storage -= physical_file.size

        if used_storage <= config.files_max_storage_size:
            break

    await _delete_virtual_files(
        await virtual_file_repository.get({'_id': {'$in': virtual_file_ids_to_delete}}),
        physical_file_repository,
        virtual_file_repository,
        physical_files_to_delete_by_id
    )

    if used_storage <= config.files_max_storage_size:
        return

    temporary_file_ids_to_delete = []

    async for temporary_file in temporary_file_repository.iter({'virtual_file_id': None}, sort_keys=('created_at',)):
        temporary_file_ids_to_delete.append(temporary_file.mongo_id)
        used_storage -= temporary_file.size

        if used_storage <= config.files_max_storage_size:
            break

    await delete_temporary_files(temporary_file_ids_to_delete, temporary_file_repository)


async def generate_embed_page(
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

    main_type = physical_file.mime_type.split('/')[0]

    meta_tags_parts = [
        f'<title>{virtual_file.name}</title>',
        f'<meta property="og:title" content="{virtual_file.name}" />',
        f'<meta property="og:description" content="File: {virtual_file.name}" />',
        f'<meta property="og:type" content="{config.open_graph_type_map.get(main_type, 'website')}" />',
        f'<meta property="og:url" content="{file_url}" />',
        f'<meta property="og:image" content="{request.url_for('get_file_thumbnail', file_id=file_id)}" />'
    ]

    if main_type == 'video':
        width, height = file_utils.get_video_resolution(build_physical_file_path(physical_file.mongo_id))
        meta_tags_parts.extend(
            (
                f'<meta property="og:video" content="{file_url}" />',
                f'<meta property="og:video:type" content="{physical_file.mime_type}" />',
                f'<meta property="og:video:width" content="{width}" />',
                f'<meta property="og:video:height" content="{height}" />'
            )
        )
    elif main_type == 'audio':
        meta_tags_parts.extend(
            (
                f'<meta property="og:audio" content="{file_url}" />',
                f'<meta property="og:audio:type" content="{physical_file.mime_type}" />'
            )
        )

    # This should not be visible to anyone, but some human user agents might contain the string 'bot' and might have skipped the initial redirect
    body_parts = [
        f'<h1>{virtual_file.name}</h1>',
        f'<p>Enlace directo: <a href="{file_url}">{file_url}</a></p>'
    ]

    match main_type:
        case 'video':
            body_parts.append(f'<video controls><source src="{file_url}" type="{physical_file.mime_type}"></video>')
        case 'audio':
            body_parts.append(f'<audio controls><source src="{file_url}" type="{physical_file.mime_type}"></audio>')
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


async def get_file_models(
    file_id: str,
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository,
    access_token_hash: str | None = None
) -> tuple[PhysicalFile, VirtualFile]:
    filter = {'_id': file_id}

    if access_token_hash:
        filter['access_token_hash'] = access_token_hash

    if (
        not (virtual_file := await virtual_file_repository.get_one(filter))
        or
        not virtual_file.physical_file_id
        or
        not (physical_file := await physical_file_repository.get_by_id(virtual_file.physical_file_id))
    ):
        raise FileNotFoundError(config.file_not_found_error_message)

    return physical_file, virtual_file


async def get_file_thumbnail_path(
    file_id: str,
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> Path:
    if (
        not (virtual_file := await virtual_file_repository.get_by_id(file_id))
        or
        not virtual_file.physical_file_id
        or
        not (physical_file := await physical_file_repository.get_by_id(virtual_file.physical_file_id))
    ):
        raise FileNotFoundError(config.file_not_found_error_message)

    main_type = physical_file.mime_type.split('/')[0]

    if main_type in {'image', 'video'}:
        if not (thumbnail_path := build_thumbnail_path(physical_file.mongo_id)).is_file():
            raise FileNotFoundError(config.file_not_found_error_message)

        return thumbnail_path

    if main_type == 'audio':
        return config.audio_thumbnail_path

    return config.default_thumbnail_path


async def get_files(
    access_token_hash: str,
    virtual_file_repository: VirtualFileRepository,
    skip: int = 0,
    limit: int | None = None
    return VirtualFiles(
        files=[
            create_virtual_file_response(virtual_file)
            async for virtual_file in virtual_file_repository.iter(
                {'access_token_hash': access_token_hash},
                sort_keys=(('created_at', pymongo.DESCENDING),),
                skip=skip,
                limit=limit
            )
) -> Files:
        ],
        total=await virtual_file_repository.count({'access_token_hash': access_token_hash})
    )


async def get_file(
    file_id: str,
    access_token_hash: str,
    physical_file_repository: PhysicalFileRepository,
    return create_virtual_file_response(
        (await get_file(file_id, physical_file_repository, virtual_file_repository, access_token_hash))[1]
    )
    virtual_file_repository: VirtualFileRepository
) -> File:
