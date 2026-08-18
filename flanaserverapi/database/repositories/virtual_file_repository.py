from pymongo.asynchronous.client_session import AsyncClientSession

from database.database_client import database
from database.repositories.repository import Repository
from models.files import VirtualFile


class VirtualFileRepository(Repository[VirtualFile, str]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database['virtual_file'], session)
