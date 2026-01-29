import aiohttp

from api.schemas.ip_geolocations import CachedIpGeolocation, IpGeolocation
from config import config
from database.repositories.cached_ip_geolocation_repository import CachedIpGeolocationRepository


async def get_ip_geolocation(session: aiohttp.ClientSession, ip: str) -> IpGeolocation | None:
    cached_ip_geolocation_repository = CachedIpGeolocationRepository()

    if cached_ip_geolocation := await cached_ip_geolocation_repository.get_by_id(ip):
        return cached_ip_geolocation.ip_geolocation

    async with session.get(
        config.ip_geolocation_endpoint,
        params={'apiKey': config.ip_geolocation_key, 'ip': ip}
    ) as response:
        if not response.ok:
            return

        ip_geolocation = IpGeolocation(**await response.json())

        await cached_ip_geolocation_repository.insert(
            CachedIpGeolocation(_id=ip_geolocation.ip, ip_geolocation=ip_geolocation)
        )

        return ip_geolocation
