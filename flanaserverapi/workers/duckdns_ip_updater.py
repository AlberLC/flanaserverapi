import asyncio
import time

import aiohttp

from config import config


async def update_ip():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(config.duckdns_ip_updater_endpoint) as response:
                if await response.text() != 'OK':
                    print(config.duckdns_ip_updater_error_message)
    except Exception as e:
        print(f'{config.duckdns_ip_updater_error_message}: {e}')


async def run_ip_updater():
    while True:
        await update_ip()
        time.sleep(config.duckdns_ip_updater_sleep)


if __name__ == '__main__':
    asyncio.run(run_ip_updater())
