import asyncio
import datetime
from collections import defaultdict
from collections.abc import AsyncGenerator, Iterable, Sequence
from pathlib import Path

from bson import ObjectId

from api.schemas.bases import MongoModel
from api.schemas.physical_file import PhysicalFile
from api.schemas.temporary_file import TemporaryFile
from api.schemas.virtual_files import VirtualFile
from config import config
from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.repository import Repository
from database.repositories.temporary_file_repository import TemporaryFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository


async def _clean_up_files(files_path: Path, valid_files_generator: AsyncGenerator[MongoModel]) -> None:
    file_ids = {str(file.mongo_id) async for file in valid_files_generator}

    for file_path in files_path.iterdir():
        if not file_path.is_file() or file_path.name in file_ids:
            continue

        try:
            file_path.unlink()
        except PermissionError:
            pass


async def _clean_up_physical_files(
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> None:
    await _clean_up_files(
        config.physical_files_path,
        _iter_valid_physical_files(physical_file_repository, virtual_file_repository)
    )


async def _clean_up_temporary_files(temporary_file_repository: TemporaryFileRepository) -> None:
    await _clean_up_files(
        config.temporary_files_path, _iter_valid_temporary_files(temporary_file_repository)
    )


async def _clean_up_virtual_files(
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> None:
    virtual_file_ids_to_delete = []

    async for virtual_file in virtual_file_repository.iter_all():
        if (
            virtual_file.physical_file_id
            and
            not await physical_file_repository.get_one({'_id': virtual_file.physical_file_id})
        ):
            virtual_file_ids_to_delete.append(virtual_file.mongo_id)

    await virtual_file_repository.delete({'_id': {'$in': virtual_file_ids_to_delete}})


async def _delete_files(files: Iterable[MongoModel], files_path: Path, repository: Repository[MongoModel]) -> None:
    ids_to_delete = []

    for file in files:
        ids_to_delete.append(file.mongo_id)

        try:
            await asyncio.to_thread((files_path / str(file.mongo_id)).unlink, missing_ok=True)
        except PermissionError:
            pass

    await repository.delete({'_id': {'$in': ids_to_delete}})


async def _delete_physical_files(
    physical_files: Iterable[PhysicalFile],
    physical_file_repository: PhysicalFileRepository
) -> None:
    await _delete_files(physical_files, config.physical_files_path, physical_file_repository)


async def _delete_temporary_files(
    temporary_files: Iterable[TemporaryFile],
    temporary_file_repository: TemporaryFileRepository
) -> None:
    await _delete_files(temporary_files, config.temporary_files_path, temporary_file_repository)


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
            for physical_file in await physical_file_repository.get({'_id': {'$in': physical_file_ids}})
        }

    physical_files_to_delete = []
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
            physical_files_to_delete.append(physical_file)

    await virtual_file_repository.delete({'_id': {'$in': virtual_file_ids_to_delete}})
    await _delete_physical_files(physical_files_to_delete, physical_file_repository)


async def _get_used_storage(
    physical_file_repository: PhysicalFileRepository,
    temporary_file_repository: TemporaryFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> int:
    used_storage = 0

    async for physical_file in _iter_valid_physical_files(physical_file_repository, virtual_file_repository):
        used_storage += physical_file.size

    async for temporary_file in _iter_valid_temporary_files(temporary_file_repository):
        used_storage += temporary_file.size

    return used_storage


async def _iter_valid_physical_files(
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> AsyncGenerator[PhysicalFile]:
    now = datetime.datetime.now(datetime.UTC)
    physical_files_to_delete_by_id = {}
    virtual_files_to_delete = []

    async for physical_file in physical_file_repository.iter_all():
        referenced_virtual_files = await virtual_file_repository.get(
            {'_id': {'$in': tuple(physical_file.virtual_file_ids)}}
        )

        if not (config.physical_files_path / str(physical_file.mongo_id)).is_file():
            virtual_files_to_delete.extend(referenced_virtual_files)
            physical_files_to_delete_by_id[physical_file.mongo_id] = physical_file
            continue

        has_valid_reference = False

        for virtual_file in referenced_virtual_files:
            if virtual_file.expires_at and now >= virtual_file.expires_at:
                virtual_files_to_delete.append(virtual_file)
            else:
                has_valid_reference = True

        if has_valid_reference:
            yield physical_file
        else:
            physical_files_to_delete_by_id[physical_file.mongo_id] = physical_file

    await _delete_virtual_files(
        virtual_files_to_delete,
        physical_file_repository,
        virtual_file_repository,
        physical_files_to_delete_by_id
    )
    await _delete_physical_files(physical_files_to_delete_by_id.values(), physical_file_repository)


async def _iter_valid_temporary_files(
    temporary_file_repository: TemporaryFileRepository
) -> AsyncGenerator[TemporaryFile]:
    now = datetime.datetime.now(datetime.UTC)
    temporary_files_to_delete = []

    async for temporary_file in temporary_file_repository.iter_all():
        file_path = config.temporary_files_path / temporary_file.mongo_id
        if (
            temporary_file.virtual_file_id
            or
            now >= temporary_file.created_at + config.temporary_files_cleanup_protection_period
            and
            not file_path.is_file()
            or
            now >= temporary_file.created_at + config.temporary_files_ttl
        ):
            temporary_files_to_delete.append(temporary_file)
            continue

        yield temporary_file

    await _delete_temporary_files(temporary_files_to_delete, temporary_file_repository)


async def clean_up_files(
    physical_file_repository: PhysicalFileRepository,
    temporary_file_repository: TemporaryFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> None:
    await _clean_up_physical_files(physical_file_repository, virtual_file_repository)
    await _clean_up_temporary_files(temporary_file_repository)
    await _clean_up_virtual_files(physical_file_repository, virtual_file_repository)


async def delete_file(
    file_id: str,
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> None:
    if not (virtual_file := await virtual_file_repository.get_by_id(file_id)):
        raise FileNotFoundError(config.file_not_found_error_message)

    await _delete_virtual_files((virtual_file,), physical_file_repository, virtual_file_repository)


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

    async for physical_file in physical_file_repository.iter_all(sort_keys=('created_at',)):
        virtual_file_ids_to_delete.extend(physical_file.virtual_file_ids)
        physical_files_to_delete_by_id[physical_file.mongo_id] = physical_file
        used_storage -= physical_file.size

        if used_storage <= config.files_max_storage_size:
            break

    virtual_files = await virtual_file_repository.get({'_id': {'$in': virtual_file_ids_to_delete}})
    await _delete_virtual_files(
        virtual_files,
        physical_file_repository,
        virtual_file_repository,
        physical_files_to_delete_by_id
    )

    if used_storage <= config.files_max_storage_size:
        return

    temporary_files_to_delete = []

    async for temporary_file in temporary_file_repository.iter({'virtual_file_id': None}, sort_keys=('created_at',)):
        temporary_files_to_delete.append(temporary_file)
        used_storage -= temporary_file.size

        if used_storage <= config.files_max_storage_size:
            break

    await _delete_temporary_files(temporary_files_to_delete, temporary_file_repository)


async def get_file(
    file_id: str,
    physical_file_repository: PhysicalFileRepository,
    virtual_file_repository: VirtualFileRepository
) -> tuple[PhysicalFile, VirtualFile]:
    if (
        not (virtual_file := await virtual_file_repository.get_by_id(file_id))
        or
        not virtual_file.physical_file_id
        or
        not (physical_file := await physical_file_repository.get_by_id(virtual_file.physical_file_id))
    ):
        raise FileNotFoundError(config.file_not_found_error_message)

    return physical_file, virtual_file
