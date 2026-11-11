import json

import aiohttp

from models.client_context import ClientContext, SystemInfo
from services import ip_geolocation_service
from utils import crypto_utils


async def build_client_context(body: bytes | ClientContext, ip: str, session: aiohttp.ClientSession) -> ClientContext:
    if isinstance(body, bytes):
        body = json.loads(crypto_utils.decrypt(body))
        system_info_data = body.get('system_info', {})
        client_code = body.get('code')

        system_info = SystemInfo(**system_info_data)
        client_context = ClientContext(system_info=system_info, client_code=client_code)
    else:
        client_context = body

    client_context.system_info.ip_geolocation = await ip_geolocation_service.get_ip_geolocation(ip, session)

    return client_context
