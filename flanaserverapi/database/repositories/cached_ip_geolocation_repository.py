from pymongo.asynchronous.client_session import AsyncClientSession

from api.schemas.ip_geolocations import CachedIpGeolocation
from database.database_client import database
from database.repositories.repository import Repository


class CachedIpGeolocationRepository(Repository[CachedIpGeolocation, str]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database['cached_ip_geolocation'], session)
