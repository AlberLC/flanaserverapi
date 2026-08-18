from bson import ObjectId
from pymongo.asynchronous.client_session import AsyncClientSession

from api.schemas.files import PhysicalFile
from database.database_client import database
from database.repositories.repository import Repository


class PhysicalFileRepository(Repository[PhysicalFile, ObjectId]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database['physical_file'], session)
