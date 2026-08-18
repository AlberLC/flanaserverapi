import datetime

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    id: str
    name: str
    url: str
    embed_url: str
    thumbnail_url: str
    width: int | None = None
    height: int | None = None
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    expires_at: datetime.datetime | None


class FilesResponse(BaseModel):
    files: list[FileResponse]
    total: int
