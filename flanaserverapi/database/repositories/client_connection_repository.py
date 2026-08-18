from bson import ObjectId
from pymongo.asynchronous.client_session import AsyncClientSession

from database.database_client import database
from database.repositories.repository import Repository
from models.client_connections import ClientConnection


class ClientConnectionRepository(Repository[ClientConnection, ObjectId]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database['client_connection'], session)
