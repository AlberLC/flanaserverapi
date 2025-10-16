import asyncio
from typing import Never

from config import config
from services import file_service


async def run_old_files_cleaner() -> Never:
    while True:
        await file_service.clean_up_old_files()
        await asyncio.sleep(config.files_cleaner_sleep)
