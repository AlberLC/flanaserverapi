from pymongo.asynchronous.client_session import AsyncClientSession

from database import database_client
from database.repositories.repository import Repository
from models.files import TemporaryFile


class TemporaryFileRepository(Repository[TemporaryFile, str]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database_client.get_collection('temporary_file'), session)
