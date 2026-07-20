import asyncio
from typing import Never

from api import api_setup
from config import config
from database.repositories.file_info_repository import FileInfoRepository
from services import file_service


async def run_old_files_cleaner() -> Never:
    file_info_repository = FileInfoRepository()
    api_setup.initialize_directories()

    while True:
        await file_service.clean_up_old_files(file_info_repository)
        await asyncio.sleep(config.files_cleaner_sleep)
