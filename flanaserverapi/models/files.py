import datetime
from typing import Annotated

from bson import ObjectId
from pydantic import Field, PlainSerializer

from models.bases import ObjectIdModel, SecretIdModel


# Some fields are intentionally duplicated across models to preserve a consistent field order.


class PhysicalFile(ObjectIdModel):
    hash: str
    size: int
    mime_type: str
    width: int | None = None
    height: int | None = None
    # noinspection PyTypeChecker
    virtual_file_ids: Annotated[set[str], PlainSerializer(list)] = set()
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))


class TemporaryFile(SecretIdModel):
    access_token_hash: str
    name: str
    size: int
    total_chunks: int
    # noinspection PyTypeChecker
    received_chunks: Annotated[set[int], PlainSerializer(list)] = set()
    is_finalizing: bool = False
    virtual_file_id: str | None = None
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    expires_in: int | None


class VirtualFile(SecretIdModel):
    access_token_hash: str
    name: str
    physical_file_id: Annotated[ObjectId, PlainSerializer(str, when_used='json')] | None = None
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    expires_at: datetime.datetime | None
