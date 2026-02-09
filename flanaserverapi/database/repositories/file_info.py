from api.schemas.file_info import FileInfo
from database.client import database
from database.repositories.repository import Repository


class FileInfoRepository(Repository[FileInfo]):
    def __init__(self) -> None:
        super().__init__(database['file_info'])
