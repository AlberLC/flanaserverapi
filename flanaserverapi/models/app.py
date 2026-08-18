from pydantic import Field

from models.bases import MongoModel
from models.licenses import LicenseConfig
from models.system_info import SystemInfo


class App(MongoModel[str]):
    version: str | None = Field(pattern=r'^\d+\.\d+\.\d+$', default=None)
    blacklisted_system_infos: list[SystemInfo] = Field(default_factory=list)
    whitelisted_system_infos: list[SystemInfo] = Field(default_factory=list)
    license_config: LicenseConfig = Field(default_factory=LicenseConfig)
