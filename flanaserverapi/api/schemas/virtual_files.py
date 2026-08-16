import datetime
from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, Field, PlainSerializer

from api.schemas.bases import SecretIdModel


class VirtualFileBase(SecretIdModel):
    name: str
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    expires_at: datetime.datetime | None


class VirtualFile(VirtualFileBase):
    access_token_hash: str
    physical_file_id: Annotated[ObjectId, PlainSerializer(str, when_used='json')] | None = None


class VirtualFileResponse(VirtualFileBase):
    url: str
    embed_url: str
    thumbnail_url: str


class VirtualFiles(BaseModel):
    files: list[VirtualFileResponse]
    total: int
