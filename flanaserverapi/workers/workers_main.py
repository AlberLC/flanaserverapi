import asyncio
from typing import Never

from database import database_setup
from workers import duckdns_ip_updater, old_files_cleaner


async def main() -> Never:
    async with database_setup.initialize_database():
        await asyncio.gather(duckdns_ip_updater.run_ip_updater(), old_files_cleaner.run_old_files_cleaner())


def run() -> Never:
    asyncio.run(main())
