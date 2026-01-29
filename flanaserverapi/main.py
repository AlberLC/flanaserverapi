from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiohttp
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.middlewares.limit_upload_size_middleware import LimitUploadSizeMiddleware
from api.routers import apps_router, embeds_router, files_router, ping_router
from config import config
from database import setup


# noinspection PyUnresolvedReferences
@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator[None]:
    await setup.initialize_database()
    app_.state.app_monitors = {}
    app_.state.http_session = aiohttp.ClientSession()

    try:
        yield
    finally:
        await app_.state.http_session.close()


app = FastAPI(lifespan=lifespan)

app.include_router(apps_router.router)
app.include_router(embeds_router.router)
app.include_router(files_router.router)
app.include_router(ping_router.router)

app.mount('/files', StaticFiles(directory='static/files'), name='files')

app.add_middleware(LimitUploadSizeMiddleware, config.upload_max_size)

if __name__ == '__main__':
    uvicorn.run('main:app', host=config.api_host, port=config.api_port, reload=True)
