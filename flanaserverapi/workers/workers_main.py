import asyncio

import duckdns_ip_updater
import old_files_cleaner


async def main() -> None:
    # noinspection PyUnreachableCode
    await asyncio.gather(duckdns_ip_updater.run_ip_updater(), old_files_cleaner.run_old_files_cleaner())


if __name__ == '__main__':
    # noinspection PyUnreachableCode
    asyncio.run(main())
