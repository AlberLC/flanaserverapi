import asyncio
import ipaddress
from typing import Any

import aiohttp

from api.schemas.ip_geolocations import CachedIpGeolocation, IpGeolocation
from config import config
from database.repositories.cached_ip_geolocation_repository import CachedIpGeolocationRepository


async def _get_geojs_data(session: aiohttp.ClientSession, ip: str) -> dict[str, Any] | None:
    async with session.get(config.geojs_endpoint, params={'ip': ip}) as response:
        if not response.ok:
            return

        geojs_raw_data = await response.json()
        geojs_raw_data = geojs_raw_data[0] if isinstance(geojs_raw_data, list) else geojs_raw_data
        geojs_raw_data.pop('ip', None)

        return geojs_raw_data


async def _get_ip_geolocation_data(session: aiohttp.ClientSession, ip: str) -> dict[str, dict[str, Any]] | None:
    async with session.get(
        config.ip_geolocation_endpoint,
        params={'apiKey': config.ip_geolocation_key, 'ip': ip}
    ) as response:
        if not response.ok:
            return

        ip_geolocation_raw_data = await response.json()
        ip_geolocation_raw_data.pop('ip', None)

        return ip_geolocation_raw_data


async def get_ip_geolocation(session: aiohttp.ClientSession, ip: str) -> IpGeolocation | None:
    if not ipaddress.ip_address(ip).is_global:
        return

    cached_ip_geolocation_repository = CachedIpGeolocationRepository()

    if cached_ip_geolocation := await cached_ip_geolocation_repository.get_by_id(ip):
        return cached_ip_geolocation.ip_geolocation

    geojs_data, ip_geolocation_data = await asyncio.gather(
        _get_geojs_data(session, ip),
        _get_ip_geolocation_data(session, ip)
    )

    if geojs_data or ip_geolocation_data:
        ip_geolocation = IpGeolocation(ip=ip, geojs_data=geojs_data, ip_geolocation_data=ip_geolocation_data)
        await cached_ip_geolocation_repository.insert(CachedIpGeolocation(_id=ip, ip_geolocation=ip_geolocation))

        return ip_geolocation
