import datetime
from typing import Any

from pydantic import BaseModel, Field


class IpGeolocation(BaseModel):
    ip: str
    geojs_data: dict[str, Any] | None = None
    ip_geolocation_data: dict[str, dict[str, Any]] | None = None

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, IpGeolocation) and self.ip == other.ip


class CachedIpGeolocation(BaseModel):
    id: str = Field(alias='_id')
    ip_geolocation: IpGeolocation
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
