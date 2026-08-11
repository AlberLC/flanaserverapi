from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import aiohttp

from config import config


@asynccontextmanager
async def initialize_api() -> AsyncGenerator[dict[str, Any]]:
    initialize_directories()

    http_session = aiohttp.ClientSession()

    try:
        yield {'app_monitors': {}, 'http_session': http_session}
    finally:
        await http_session.close()


def initialize_directories() -> None:
    config.apps_path.mkdir(parents=True, exist_ok=True)
    config.physical_files_path.mkdir(parents=True, exist_ok=True)
    config.temporary_files_path.mkdir(parents=True, exist_ok=True)
    config.thumbnails_path.mkdir(parents=True, exist_ok=True)
