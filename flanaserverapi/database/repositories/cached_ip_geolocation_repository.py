from api.schemas.ip_geolocations import CachedIpGeolocation
from database.client import database
from database.repositories.repository import Repository


class CachedIpGeolocationRepository(Repository[CachedIpGeolocation]):
    def __init__(self) -> None:
        super().__init__(database['cached_ip_geolocation'])
