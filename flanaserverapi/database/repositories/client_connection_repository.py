from api.schemas.client_connections import ClientConnection
from database.client import database
from database.repositories.repository import Repository


class ClientConnectionRepository(Repository[ClientConnection]):
    def __init__(self) -> None:
        super().__init__(database['client_connection'])
