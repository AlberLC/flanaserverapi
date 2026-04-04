from collections.abc import Generator
from typing import Any, Self

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

    def _iter_attributes_comparisons(self, other: Self) -> Generator[bool]:
        for attribute_name in config.system_info_identifying_attributes:
            if other_attribute := getattr(other, attribute_name):
                yield getattr(self, attribute_name) == other_attribute

    def equals_partially(self, other: Any) -> bool:
        return isinstance(other, SystemInfo) and any(self._iter_attributes_comparisons(other))

    def has_matching_attributes(self, other: Any) -> bool:
        return isinstance(other, SystemInfo) and all(self._iter_attributes_comparisons(other))
