import datetime
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer

from api.serializers import to_raw_paths
from custom_types import AppId
from models.bases import ObjectIdModel
from models.system_info import SystemInfo


class AppInstallationPaths(BaseModel):
    directory_paths: Annotated[list[Path], PlainSerializer(to_raw_paths)] = Field(default_factory=list)
    compressed_paths: Annotated[list[Path], PlainSerializer(to_raw_paths)] = Field(default_factory=list)


class ClientConnection(ObjectIdModel):
    app_id: AppId
    system_info: SystemInfo | None = None
    app_installation_paths: AppInstallationPaths = Field(default_factory=AppInstallationPaths)
    date: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
