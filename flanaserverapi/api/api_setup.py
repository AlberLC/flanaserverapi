import shutil
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI

from config import config


@asynccontextmanager
async def initialize_api(app: FastAPI) -> AsyncGenerator[None]:
    app.state.app_monitors = {}
    app.state.http_session = aiohttp.ClientSession()

    config.apps_path.mkdir(parents=True, exist_ok=True)
    config.files_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config.audio_thumbnail_path, config.files_path)
    shutil.copy2(config.default_thumbnail_path, config.files_path)

    try:
        yield
    finally:
        await app.state.http_session.close()
