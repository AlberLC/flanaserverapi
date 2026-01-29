from api.schemas.app import App
from database.client import database
from database.repositories.repository import Repository


class AppRepository(Repository[App]):
    def __init__(self) -> None:
        super().__init__(database['app'])
