from pymongo.asynchronous.client_session import AsyncClientSession

from api.schemas.virtual_files import VirtualFile
from database.database_client import database
from database.repositories.repository import Repository


class VirtualFileRepository(Repository[VirtualFile, str]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database['virtual_file'], session)
