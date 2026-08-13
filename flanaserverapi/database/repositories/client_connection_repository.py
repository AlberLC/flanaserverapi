from pymongo.asynchronous.client_session import AsyncClientSession

from api.schemas.client_connections import ClientConnection
from database.database_client import database
from database.repositories.repository import Repository


class ClientConnectionRepository(Repository[ClientConnection]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database['client_connection'], session)
