import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routers import flanaarena, flanacs, flanatrigo
from config import config

app = FastAPI()
app.include_router(flanaarena.router)
app.include_router(flanacs.router)
app.include_router(flanatrigo.router)

app.mount('/files', StaticFiles(directory='static/files'), name='files')

if __name__ == '__main__':
    uvicorn.run('main:app', host=config.api_host, port=config.api_port)
