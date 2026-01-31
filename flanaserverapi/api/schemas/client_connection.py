import datetime

from pydantic import Field

from api.schemas.app_installation_paths import AppInstallationPaths
from api.schemas.bases import ObjectIdModel
from api.schemas.system_info import SystemInfo
from custom_types import AppId


class ClientConnection(ObjectIdModel):
    app_id: AppId
    system_info: SystemInfo | None = None
    app_installation_paths: AppInstallationPaths = Field(default_factory=AppInstallationPaths)
    date: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
