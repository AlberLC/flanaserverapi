from pymongo.asynchronous.client_session import AsyncClientSession

from api.schemas.files import TemporaryFile
from database.database_client import database
from database.repositories.repository import Repository


class TemporaryFileRepository(Repository[TemporaryFile, str]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database['temporary_file'], session)
