from pymongo.asynchronous.client_session import AsyncClientSession

from api.schemas.app import App
from database.database_client import database
from database.repositories.repository import Repository


class AppRepository(Repository[App, str]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database['app'], session)
