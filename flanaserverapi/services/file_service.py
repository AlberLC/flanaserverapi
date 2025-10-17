import asyncio
import datetime
import json
import shutil
import urllib.parse
from collections.abc import AsyncIterator
from pathlib import Path

import fastapi.encoders
from fastapi import UploadFile

from api.schemas.file_info import FileInfo
from config import config


async def clean_up_old_files() -> None:
    async for _ in iter_valid_files_metadata():
        pass


async def delete_file(file_name: str) -> None:
    file_path = config.files_path / Path(urllib.parse.unquote(file_name)).name

    if not file_path.is_file():
        raise FileNotFoundError(f'Archivo `{file_name}` no encontrado')

    await asyncio.to_thread(file_path.unlink)


async def enforce_storage_limit() -> None:
    used_storage = await get_used_storage()

    if used_storage <= config.files_max_storage_size:
        return

    files_metadata = json.loads(config.files_metadata_path.read_text())
    # noinspection PyShadowingNames
    files_info = sorted(
        (FileInfo(**file_info_data) for file_info_data in files_metadata.values()),
        key=lambda file_info: file_info.created_at
    )

    for file_info in files_info:
        file_path = config.files_path / file_info.file_name

        try:
            await asyncio.to_thread(file_path.unlink)
        except PermissionError:
            continue

        used_storage -= file_info.size
        files_metadata.pop(file_info.file_name)

        if used_storage <= config.files_max_storage_size:
            break

    config.files_metadata_path.write_text(json.dumps(files_metadata, indent=2))


async def get_used_storage() -> int:
    used_storage = 0

    async for file_info in iter_valid_files_metadata():
        used_storage += file_info.size

    return used_storage


async def iter_valid_files_metadata() -> AsyncIterator[FileInfo]:
    if not config.files_metadata_path.is_file():
        config.files_metadata_path.write_text('{}')

    files_metadata = json.loads(config.files_metadata_path.read_text())
    updated_files_metadata = {}
    now = datetime.datetime.now(datetime.UTC)

    for file_name, file_info_data in files_metadata.items():
        file_info = FileInfo(**file_info_data)
        file_path = config.files_path / file_name

        if not file_path.is_file():
            continue

        if file_info.expires_at and now >= file_info.expires_at:
            try:
                await asyncio.to_thread(file_path.unlink)
            except PermissionError:
                pass
            else:
                continue

        yield file_info

        updated_files_metadata[file_name] = file_info_data

    config.files_metadata_path.write_text(json.dumps(updated_files_metadata, indent=2))


async def save_file(file: UploadFile, expires_in: int | None) -> FileInfo:
    file_name = Path(urllib.parse.unquote(file.filename)).name

    file_path = config.files_path / file_name

    with open(file_path, 'wb') as new_file:
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
        size=file_path.stat().st_size,
        content_type=file.content_type,
        expires_at=expires_at
    )

    if not config.files_metadata_path.is_file():
        config.files_metadata_path.write_text('{}')

    files_metadata = json.loads(config.files_metadata_path.read_text())
    files_metadata[file_name] = fastapi.encoders.jsonable_encoder(file_info)
    config.files_metadata_path.write_text(json.dumps(files_metadata, indent=2))

    await enforce_storage_limit()

    return file_info
