from api.schemas.app import App
from database.client import database
from database.repositories.repository import Repository


class AppRepository(Repository[App]):
    def __init__(self) -> None:
        super().__init__(database['apps'])

    async def get_by_id(self, id: str) -> App:
        return await self._collection.find_one({'_id': id})
