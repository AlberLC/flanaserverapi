import datetime

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    file_name: str
    url: str
    embed_url: str
    size: int
    content_type: str | None
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    expires_at: datetime.datetime | None = None
