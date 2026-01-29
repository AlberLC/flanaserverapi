import asyncio
from typing import Never

import aiohttp

from config import config


async def update_ip(session: aiohttp.ClientSession) -> None:
    try:
        async with session.get(
            config.duckdns_ip_updater_endpoint,
            params={'domains': config.subdomain, 'token': config.duckdns_key, 'ip': ''}
        ) as response:
            if await response.text() != 'OK':
                print(config.duckdns_ip_updater_error_message)
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        print(f'{config.duckdns_ip_updater_error_message}: {e}')


async def run_ip_updater() -> Never:
    async with aiohttp.ClientSession() as session:
        while True:
            await update_ip(session)
            await asyncio.sleep(config.duckdns_ip_updater_sleep)
