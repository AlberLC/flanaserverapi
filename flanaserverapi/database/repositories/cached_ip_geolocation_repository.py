from pymongo.asynchronous.client_session import AsyncClientSession

from database import database_client
from database.repositories.repository import Repository
from models.ip_geolocations import CachedIpGeolocation


class CachedIpGeolocationRepository(Repository[CachedIpGeolocation, str]):
    def __init__(self, session: AsyncClientSession | None = None) -> None:
        super().__init__(database_client.get_collection('cached_ip_geolocation'), session)
