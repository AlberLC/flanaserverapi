import asyncio
import datetime
import filecmp
import hashlib
import io
import math
from pathlib import Path

import pymongo.errors
from PIL import Image, ImageOps

from api.schemas.create_upload_request import CreateUploadRequest
from api.schemas.create_upload_response import CreateUploadResponse
from api.schemas.physical_file import PhysicalFile
from api.schemas.temporary_file import TemporaryFile
from api.schemas.upload_state import UploadState
from api.schemas.virtual_files import VirtualFile, VirtualFileResponse
from config import config
from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.temporary_file_repository import TemporaryFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository
from exceptions import IncompleteUploadError, InvalidChunkError, UploadFinalizedError, UploadNotFoundError
from services import file_service
from utils import crypto_utils, file_utils


async def _create_physical_file(
    temporary_file: TemporaryFile,
    virtual_file_id: str,
    physical_file_repository: PhysicalFileRepository
) -> PhysicalFile:
    temporary_file_path = file_service.build_temporary_file_path(temporary_file.mongo_id)

    try:
        file_hash = await asyncio.to_thread(crypto_utils.hash_file, temporary_file_path)
    except FileNotFoundError:
        raise UploadNotFoundError

    if (
        (physical_file := await physical_file_repository.get_one({'hash': file_hash}))
        and
        await asyncio.to_thread(
            filecmp.cmp,
            temporary_file_path,
            file_service.build_physical_file_path(physical_file.mongo_id),
            shallow=False
        )
    ):
        await physical_file_repository.partial_update_one(
            {'_id': physical_file.mongo_id}, {'$addToSet': {'virtual_file_ids': virtual_file_id}}
        )
    else:
        physical_file = await physical_file_repository.insert_one(
            PhysicalFile(
                hash=file_hash,
                size=temporary_file.size,
                mime_type=await asyncio.to_thread(file_utils.get_mime_type, temporary_file_path),
                virtual_file_ids={virtual_file_id}
            )
        )

    await asyncio.to_thread(temporary_file_path.move, file_service.build_physical_file_path(physical_file.mongo_id))

    return physical_file


async def _create_virtual_file(
    temporary_file: TemporaryFile,
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> VirtualFile:
    while True:
        mongo_id = crypto_utils.create_id()

        try:
            virtual_file = await virtual_file_repository.insert_one(
                VirtualFile(
                    _id=mongo_id,
                    name=temporary_file.name,
                    expires_at=temporary_file.expires_at
                )
            )
        except pymongo.errors.DuplicateKeyError:
            pass
        else:
            break

    physical_file = await _create_physical_file(temporary_file, virtual_file.mongo_id, physical_file_repository)
    _create_thumbnail(physical_file)
    virtual_file.physical_file_id = physical_file.mongo_id
    await virtual_file_repository.update_one_by_id(virtual_file)

    return virtual_file


def _create_thumbnail(physical_file: PhysicalFile) -> None:
    main_type = physical_file.mime_type.split('/')[0]

    if main_type not in {'image', 'video'}:
        return

    physical_file_path = file_service.build_physical_file_path(physical_file.mongo_id)

    if main_type == 'video':
        image_source = io.BytesIO(file_utils.extract_video_frame(physical_file_path))
    else:
        image_source = physical_file_path

    with Image.open(image_source) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail((config.thumbnails_max_size, config.thumbnails_max_size), Image.Resampling.LANCZOS)
        image.save(
            file_service.build_thumbnail_path(physical_file.mongo_id),
            quality=config.thumbnails_quality,
            method=config.thumbnails_method
        )


async def _store_chunk(
    upload_id: str,
    chunk_index: int,
    chunk_bytes: bytes,
    temporary_file_repository: TemporaryFileRepository
) -> TemporaryFile | None:
    await asyncio.to_thread(_write_chunk, chunk_index, chunk_bytes, file_service.build_temporary_file_path(upload_id))
    await temporary_file_repository.partial_update_one(
        {'_id': upload_id}, {'$addToSet': {'received_chunks': chunk_index}}
    )


def _validate_chunk(chunk_index: int, chunk_checksum: str, chunk_bytes: bytes, temporary_file: TemporaryFile) -> None:
    last_chunk_index = temporary_file.total_chunks - 1

    if (
        chunk_index != last_chunk_index
        and
        (not 0 <= chunk_index < last_chunk_index or len(chunk_bytes) != config.upload_chunk_size)
        or
        chunk_index == last_chunk_index
        and
        len(chunk_bytes) != (temporary_file.size % config.upload_chunk_size or config.upload_chunk_size)
        or
        hashlib.sha256(chunk_bytes).hexdigest() != chunk_checksum
    ):
        raise InvalidChunkError


def _write_chunk(chunk_index: int, chunk_bytes: bytes, temporary_file_path: Path) -> None:
    if not temporary_file_path.is_file():
        temporary_file_path.touch()

    with open(temporary_file_path, 'r+b') as temporary_file_stream:
        temporary_file_stream.seek(chunk_index * config.upload_chunk_size)
        temporary_file_stream.write(chunk_bytes)


async def cancel_upload(upload_id: str, temporary_file_repository: TemporaryFileRepository) -> None:
    if not await temporary_file_repository.partial_update_one(
        {'_id': upload_id, 'is_finalizing': False, 'virtual_file_id': None}, {'$set': {'is_finalizing': True}}
    ):
        if await temporary_file_repository.get_by_id(upload_id):
            raise UploadFinalizedError

        raise UploadNotFoundError

    await temporary_file_repository.delete_by_id(upload_id)
    await asyncio.to_thread(file_service.build_temporary_file_path(upload_id).unlink)


async def complete_upload(
    upload_id: str,
    physical_file_repository: PhysicalFileRepository,
    temporary_file_repository: TemporaryFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> VirtualFileResponse:
    if not (temporary_file := await temporary_file_repository.get_by_id(upload_id)):
        raise UploadNotFoundError

    if temporary_file.virtual_file_id:
        if virtual_file := await virtual_file_repository.get_by_id(temporary_file.virtual_file_id):
            return file_service.create_virtual_file_response(virtual_file)
        else:
            raise UploadNotFoundError

    if len(temporary_file.received_chunks) != temporary_file.total_chunks:
        raise IncompleteUploadError

    if not (
        temporary_file := await temporary_file_repository.partial_update_one(
            {'_id': upload_id, 'is_finalizing': False}, {'$set': {'is_finalizing': True}}
        )
    ):
        raise UploadFinalizedError

    try:
        virtual_file = await _create_virtual_file(temporary_file, physical_file_repository, virtual_file_repository)
        temporary_file.virtual_file_id = virtual_file.mongo_id
    finally:
        temporary_file.is_finalizing = False
        await temporary_file_repository.update_one_by_id(temporary_file)

    return file_service.create_virtual_file_response(virtual_file)


async def create_upload(
    create_upload_request: CreateUploadRequest,
    physical_file_repository: PhysicalFileRepository,
    temporary_file_repository: TemporaryFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> CreateUploadResponse:
    now = datetime.datetime.now(datetime.UTC)

    if create_upload_request.file_expires_in is None:
        expires_at = None
    else:
        expires_at = now + datetime.timedelta(seconds=create_upload_request.file_expires_in)

    while True:
        try:
            temporary_file = await temporary_file_repository.insert_one(
                TemporaryFile(
                    name=create_upload_request.file_name,
                    size=create_upload_request.file_size,
                    total_chunks=math.ceil(create_upload_request.file_size / config.upload_chunk_size),
                    expires_at=expires_at
                )
            )
        except pymongo.errors.DuplicateKeyError:
            pass
        else:
            break

    await file_service.enforce_storage_limit(
        physical_file_repository,
        temporary_file_repository,
        virtual_file_repository
    )

    return CreateUploadResponse(id=temporary_file.mongo_id, chunk_size=config.upload_chunk_size)


async def get_upload_state(upload_id: str, temporary_file_repository: TemporaryFileRepository) -> UploadState:
    if not (temporary_file := await temporary_file_repository.get_by_id(upload_id)):
        raise UploadNotFoundError

    return UploadState(chunk_size=config.upload_chunk_size, uploaded_chunks=sorted(temporary_file.received_chunks))


async def process_chunk(
    upload_id: str,
    chunk_index: int,
    chunk_checksum: str,
    chunk_bytes: bytes,
    temporary_file_repository: TemporaryFileRepository
) -> None:
    if not (temporary_file := await temporary_file_repository.get_by_id(upload_id)):
        raise UploadNotFoundError

    _validate_chunk(chunk_index, chunk_checksum, chunk_bytes, temporary_file)

    if chunk_index in temporary_file.received_chunks:
        return

    await _store_chunk(
        upload_id,
        chunk_index,
        chunk_bytes,
        temporary_file_repository
    )
