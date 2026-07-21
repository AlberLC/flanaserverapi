import datetime
import multiprocessing

import gunicorn.arbiter
from uvicorn_worker import UvicornWorker

from config import config as config_
from workers import workers_main


class WSUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {**UvicornWorker.CONFIG_KWARGS, 'ws_ping_interval': datetime.timedelta(hours=1).total_seconds()}


def on_starting(_arbiter: gunicorn.arbiter.Arbiter) -> None:
    multiprocessing.Process(target=workers_main.run, daemon=True).start()


bind = f'{config_.api_host}:{config_.api_port}'
preload_app = True
worker_class = WSUvicornWorker
workers = 4
