from pydantic import BaseModel, Field

from api.schemas.licenses import LicenseConfig
from api.schemas.system_info import SystemInfo


class App(BaseModel):
    id: str = Field(alias='_id')
    version: str | None = Field(pattern=r'^\d+\.\d+\.\d+$', default=None)
    blacklisted_system_infos: list[SystemInfo] = Field(default_factory=list)
    whitelisted_system_infos: list[SystemInfo] = Field(default_factory=list)
    license_config: LicenseConfig = Field(default_factory=LicenseConfig)
