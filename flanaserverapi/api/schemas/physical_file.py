import datetime
from typing import Annotated

from pydantic import Field, PlainSerializer

from api.schemas.bases import ObjectIdModel


class PhysicalFile(ObjectIdModel):
    hash: str
    size: int
    mime_type: str
    # noinspection PyTypeChecker
    virtual_file_ids: Annotated[set[str], PlainSerializer(list)] = set()
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
