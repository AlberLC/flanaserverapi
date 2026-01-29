import asyncio
from asyncio import Condition

from api.dependencies import app_dependencies
from api.schemas.app import App
from config import config
from database.repositories.app_repository import AppRepository


class AppMonitor:
    def __init__(self, app_id: str) -> None:
        self._app_id = app_id

        self._app: App | None = None
        self._app_fetcher_task: asyncio.Task[None] | None = None
        self._app_repository = AppRepository()
        self._client_counter = 0
        self._condition = Condition()

    async def _run_app_fetcher(self) -> None:
        while True:
            async with self._condition:
                self._app = await app_dependencies.get_app(self._app_id, self._app_repository)
                self._condition.notify_all()

            await asyncio.sleep(config.app_monitor_sleep)

    def add_client(self) -> None:
        self._client_counter += 1

        if not self._app_fetcher_task:
            self._app_fetcher_task = asyncio.create_task(self._run_app_fetcher())

    def remove_client(self) -> None:
        if not self._client_counter:
            return

        self._client_counter -= 1

        if not self._client_counter:
            self._app_fetcher_task.cancel()
            self._app_fetcher_task = None

    async def wait_app(self) -> App:
        async with self._condition:
            await self._condition.wait()

            return self._app
