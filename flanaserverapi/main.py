import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routers import embeds_router, files_router, flanaarena_router, flanacs_router, flanatrigo_router
from config import config

app = FastAPI()

app.include_router(embeds_router.router)
app.include_router(files_router.router)
app.include_router(flanaarena_router.router)
app.include_router(flanacs_router.router)
app.include_router(flanatrigo_router.router)

app.mount('/files', StaticFiles(directory='static/files'), name='files')

if __name__ == '__main__':
    uvicorn.run('main:app', host=config.api_host, port=config.api_port)
