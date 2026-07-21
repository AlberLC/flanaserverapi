from api.schemas.physical_file import PhysicalFile
from database.client import database
from database.repositories.repository import Repository


class PhysicalFileRepository(Repository[PhysicalFile]):
    def __init__(self) -> None:
        super().__init__(database['physical_file'])
