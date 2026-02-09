import datetime
import multiprocessing

import gunicorn.arbiter
from uvicorn_worker import UvicornWorker

from workers import workers_main


class WSUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {**UvicornWorker.CONFIG_KWARGS, 'ws_ping_interval': datetime.timedelta(hours=1).total_seconds()}


def on_starting(_arbiter: gunicorn.arbiter.Arbiter) -> None:
    multiprocessing.Process(target=workers_main.run, daemon=True).start()


bind = '0.0.0.0:5210'
preload_app = True
worker_class = WSUvicornWorker
workers = 4
