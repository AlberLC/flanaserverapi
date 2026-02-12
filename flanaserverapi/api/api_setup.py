import shutil
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import aiohttp
from fastapi import FastAPI

from config import config


@asynccontextmanager
async def initialize_api(_: FastAPI) -> AsyncGenerator[dict[str, Any]]:
    config.apps_path.mkdir(parents=True, exist_ok=True)
    config.static_images_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config.audio_thumbnail_path, config.static_images_path)
    shutil.copy2(config.default_thumbnail_path, config.static_images_path)

    http_session = aiohttp.ClientSession()

    try:
        yield {'app_monitors': {}, 'http_session': http_session}
    finally:
        await http_session.close()
