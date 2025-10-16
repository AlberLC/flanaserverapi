import asyncio

import aiohttp

from config import config


async def update_ip() -> None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(config.duckdns_ip_updater_endpoint) as response:
                if await response.text() != 'OK':
                    print(config.duckdns_ip_updater_error_message)
    except Exception as e:
        print(f'{config.duckdns_ip_updater_error_message}: {e}')


async def run_ip_updater() -> None:
    while True:
        await update_ip()
        await asyncio.sleep(config.duckdns_ip_updater_sleep)
