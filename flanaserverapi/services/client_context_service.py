import json

import aiohttp

from api.schemas.client_context import ClientContext, SystemInfo
from services import ip_geolocation_service
from utils import crypto


async def build_client_context(encrypted_body: bytes, session: aiohttp.ClientSession, ip: str) -> ClientContext:
    body = json.loads(crypto.decrypt(encrypted_body))
    system_info_data = body.get('system_info', {})
    client_code = body.get('code')

    system_info = SystemInfo(**system_info_data)
    system_info.ip_geolocation = await ip_geolocation_service.get_ip_geolocation(session, ip)

    return ClientContext(system_info=system_info, client_code=client_code)
