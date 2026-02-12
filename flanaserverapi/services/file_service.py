import asyncio
import datetime
import shutil
from collections.abc import AsyncIterator, Iterable
from pathlib import Path

from fastapi import UploadFile

from api.schemas.file_info import FileInfo
from config import config
from database.repositories.file_info import FileInfoRepository
from utils import files


async def _delete_file_infos(file_info_repository: FileInfoRepository, file_infos: Iterable[FileInfo]) -> None:
    ids_to_delete = []

    for file_info in file_infos:
        try:
            await asyncio.to_thread((config.files_path / file_info.file_name).unlink, missing_ok=True)
        except PermissionError:
            pass

        ids_to_delete.append(file_info.id)

    if ids_to_delete:
        await file_info_repository.delete({'_id': {'$in': ids_to_delete}})


async def clean_up_old_files(file_info_repository: FileInfoRepository) -> None:
    saved_file_names = set()

    async for file_info in iter_valid_file_infos(file_info_repository):
        saved_file_names.add(file_info.file_name)

    for file_path in config.files_path.iterdir():
        if not file_path.is_file() or file_path.name in saved_file_names:
            continue

        try:
            file_path.unlink()
        except PermissionError:
            pass


async def delete_file(file_path: str | Path) -> None:
    file_path = Path(file_path)
    file_name = Path(file_path).name

    if not file_path.is_file():
        raise FileNotFoundError(f'Archivo {file_name} no encontrado')

    await asyncio.to_thread(file_path.unlink)
    await FileInfoRepository().delete_one({'file_name': file_name})


async def enforce_storage_limit(file_info_repository: FileInfoRepository) -> None:
    used_storage = await get_used_storage(file_info_repository)

    if used_storage <= config.files_max_storage_size:
        return

    file_infos_to_delete = []

    async for file_info in file_info_repository.iter_all(sort_keys=('created_at',)):
        file_infos_to_delete.append(file_info)
        used_storage -= file_info.size

        if used_storage <= config.files_max_storage_size:
            break

    await _delete_file_infos(file_info_repository, file_infos_to_delete)


async def get_used_storage(file_info_repository: FileInfoRepository) -> int:
    used_storage = 0

    async for file_info in iter_valid_file_infos(file_info_repository):
        used_storage += file_info.size

    return used_storage


async def iter_valid_file_infos(file_info_repository: FileInfoRepository) -> AsyncIterator[FileInfo]:
    now = datetime.datetime.now(datetime.UTC)
    file_infos_to_delete = []

    async for file_info in file_info_repository.iter_all():
        file_path = config.files_path / file_info.file_name

        if not file_path.is_file() or file_info.expires_at and now >= file_info.expires_at:
            file_infos_to_delete.append(file_info)
            continue

        yield file_info

    await _delete_file_infos(file_info_repository, file_infos_to_delete)


async def save_file(file: UploadFile, expires_in: int | None) -> FileInfo:
    file_name = files.normalize_file_name(file.filename)
    new_file_path = config.files_path / file_name

    with open(new_file_path, 'wb') as new_file:
        # noinspection PyTypeChecker
        await asyncio.to_thread(shutil.copyfileobj, file.file, new_file)

    if expires_in is None:
        expires_at = None
    else:
        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=expires_in)

    file_info = FileInfo(
        file_name=file_name,
        url=f'/files/{file_name}',
        embed_url=f'/embeds/{file_name}',
        size=new_file_path.stat().st_size,
        content_type=file.content_type,
        expires_at=expires_at
    )

    file_info_repository = FileInfoRepository()

    await file_info_repository.delete_one({'file_name': file_info.file_name})
    await file_info_repository.insert(file_info)

    await enforce_storage_limit(file_info_repository)

    return file_info
