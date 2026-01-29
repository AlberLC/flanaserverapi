import aiohttp
from starlette.requests import HTTPConnection


async def get_http_session(http_connection: HTTPConnection) -> aiohttp.ClientSession:
    return http_connection.app.state.http_session


async def get_ip(http_connection: HTTPConnection) -> str:
    return http_connection.client.host
