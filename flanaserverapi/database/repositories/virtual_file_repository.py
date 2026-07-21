from api.schemas.virtual_files import VirtualFile
from database.client import database
from database.repositories.repository import Repository


class VirtualFileRepository(Repository[VirtualFile]):
    def __init__(self) -> None:
        super().__init__(database['virtual_file'])
