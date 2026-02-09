import asyncio
from typing import Never

from workers import duckdns_ip_updater, old_files_cleaner


async def main() -> Never:
    # noinspection PyUnreachableCode
    await asyncio.gather(duckdns_ip_updater.run_ip_updater(), old_files_cleaner.run_old_files_cleaner())


def run() -> Never:
    # noinspection PyUnreachableCode
    asyncio.run(main())
