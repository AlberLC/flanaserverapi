from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import api_setup
from api.middlewares.limit_upload_size_middleware import LimitUploadSizeMiddleware
from api.routers import apps_router, embeds_router, files_router, ping_router
from config import config
from database import database_setup


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator[dict[str, Any]]:
    await database_setup.initialize_database()

    async with api_setup.initialize_api(app_) as state:
        yield state


app = FastAPI(lifespan=lifespan)

app.include_router(apps_router.router)
app.include_router(embeds_router.router)
app.include_router(files_router.router)
app.include_router(ping_router.router)

app.mount('/files', StaticFiles(directory='static/files', check_dir=False), name='files')

app.add_middleware(LimitUploadSizeMiddleware, config.upload_max_size)

if __name__ == '__main__':
    uvicorn.run('main:app', host=config.api_host, port=config.api_port, reload=True)
