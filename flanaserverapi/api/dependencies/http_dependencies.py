from typing import Annotated

import aiohttp
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.requests import HTTPConnection

from config import config

get_credentials = HTTPBearer()


async def check_bearer_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_credentials)]) -> None:
    if credentials.credentials != config.api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def get_http_session(http_connection: HTTPConnection) -> aiohttp.ClientSession:
    return http_connection.state.http_session


async def get_ip(http_connection: HTTPConnection) -> str:
    return http_connection.client.host
