import uvicorn
from fastapi import FastAPI

from api.routers import flanacs, flanatrigo
from config import config

app = FastAPI()
app.include_router(flanacs.router)
app.include_router(flanatrigo.router)

if __name__ == '__main__':
    uvicorn.run('main:app', host=config.api_host, port=config.api_port)
