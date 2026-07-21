import datetime
from typing import Annotated

from pydantic import Field, PlainSerializer

from api.schemas.bases import SecretIdModel


class TemporaryFile(SecretIdModel):
    name: str
    size: int
    mime_type: str
    total_chunks: int
    # noinspection PyTypeChecker
    received_chunks: Annotated[set[int], PlainSerializer(list)] = set()
    is_finalizing: bool = False
    virtual_file_id: str | None = None
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    expires_at: datetime.datetime | None
