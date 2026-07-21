from api.schemas.temporary_file import TemporaryFile
from database.client import database
from database.repositories.repository import Repository


class TemporaryFileRepository(Repository[TemporaryFile]):
    def __init__(self) -> None:
        super().__init__(database['temporary_file'])
