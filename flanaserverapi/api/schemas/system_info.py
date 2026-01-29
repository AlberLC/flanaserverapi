from typing import Any

from pydantic import BaseModel

from api.schemas.ip_geolocations import IpGeolocation
from config import config


class SystemInfo(BaseModel):
    username: str | None = None
    hostname: str | None = None
    mac_address: str | None = None
    system: str | None = None
    release: str | None = None
    version: str | None = None
    machine: str | None = None
    processor: str | None = None
    ip_geolocation: IpGeolocation | None = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SystemInfo):
            return False

        for attribute_name in config.system_info_identifying_attributes:
            self_attribute = getattr(self, attribute_name)
            other_attribute = getattr(other, attribute_name)

            if self_attribute and other_attribute and self_attribute == other_attribute:
                return True

        return False
