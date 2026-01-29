import datetime

from uvicorn_worker import UvicornWorker


class WSUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {**UvicornWorker.CONFIG_KWARGS, 'ws_ping_interval': datetime.timedelta(hours=1).total_seconds()}
