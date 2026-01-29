import datetime
from typing import Any

from pydantic import BaseModel, Field


class IpGeolocation(BaseModel):
    ip: str
    location: dict[str, Any]
    country_metadata: dict[str, Any]
    currency: dict[str, str]

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, IpGeolocation) and self.ip == other.ip


class CachedIpGeolocation(BaseModel):
    id: str = Field(alias='_id')
    ip_geolocation: IpGeolocation
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
