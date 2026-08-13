from pymongo.asynchronous.client_session import AsyncClientSession

from api.schemas.physical_file import PhysicalFile
from database.database_client import database
from database.repositories.repository import Repository


class PhysicalFileRepository(Repository[PhysicalFile]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database['physical_file'], session)
