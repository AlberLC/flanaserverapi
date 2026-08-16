import hashlib
import secrets
from collections.abc import Callable
from typing import Annotated

import aiohttp
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.requests import HTTPConnection

from config import config


def check_access_token(expected_access_token_id: str) -> Callable[[tuple[str, str]], None]:
    def wrapper(access_token_parts: Annotated[tuple[str, str], Depends(get_access_token_parts)]) -> None:
        access_token_id, access_token_hash = access_token_parts
        expected_access_token_hash = config.access_token_hashes.get(access_token_id, config.dummy_access_token_hash)

        if not secrets.compare_digest(access_token_hash, expected_access_token_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)

        if access_token_id != expected_access_token_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN)

    return wrapper


def get_access_token_hash(access_token_parts: Annotated[tuple[str, str], Depends(get_access_token_parts)]) -> str:
    return access_token_parts[1]


def get_access_token_id(access_token_parts: Annotated[tuple[str, str], Depends(get_access_token_parts)]) -> str:
    return access_token_parts[0]


def get_access_token_parts(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_credentials)]
) -> tuple[str, str]:
    try:
        access_token_id, access_token_secret = credentials.credentials.split('.', maxsplit=1)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    if not access_token_secret:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    return access_token_id, hashlib.sha256(access_token_secret.encode()).hexdigest()


def get_http_session(http_connection: HTTPConnection) -> aiohttp.ClientSession:
    return http_connection.state.http_session


def get_ip(http_connection: HTTPConnection) -> str:
    return http_connection.client.host


get_credentials = HTTPBearer()
