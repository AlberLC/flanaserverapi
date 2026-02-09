import asyncio
from typing import Never

from config import config
from database.repositories.file_info import FileInfoRepository
from services import file_service


async def run_old_files_cleaner() -> Never:
    file_info_repository = FileInfoRepository()

    while True:
        await file_service.clean_up_old_files(file_info_repository)
        await asyncio.sleep(config.files_cleaner_sleep)
