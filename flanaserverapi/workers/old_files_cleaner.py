import asyncio
from typing import Never

from api import api_setup
from config import config
from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.temporary_file_repository import TemporaryFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository
from services import file_service


async def run_old_files_cleaner() -> Never:
    api_setup.initialize_directories()

    physical_file_repository = PhysicalFileRepository()
    temporary_file_repository = TemporaryFileRepository()
    virtual_file_repository = VirtualFileRepository()

    while True:
        await file_service.clean_up_files(physical_file_repository, temporary_file_repository, virtual_file_repository)
        await asyncio.sleep(config.files_cleaner_sleep)
