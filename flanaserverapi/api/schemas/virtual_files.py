import datetime
from typing import Annotated

from bson import ObjectId
from pydantic import Field, PlainSerializer

from api.schemas.bases import SecretIdModel


class VirtualFileResponse(SecretIdModel):
    name: str
    url: str
    embed_url: str
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    expires_at: datetime.datetime | None


class VirtualFile(VirtualFileResponse):
    physical_file_id: Annotated[ObjectId, PlainSerializer(str, when_used='json')] | None = None
