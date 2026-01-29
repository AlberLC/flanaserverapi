from pathlib import Path
from typing import Annotated

import aiohttp
from fastapi import Body, Depends, HTTPException, status
from starlette.requests import HTTPConnection

from api.dependencies.http_dependencies import get_http_session, get_ip
from api.schemas.app import App
from api.schemas.client_context import ClientContext
from config import config
from custom_types import AppId
from database.repositories.app_repository import AppRepository
from enums import ReleaseType
from services import client_context_service
from services.app_monitor import AppMonitor


async def get_app(app_id: AppId, app_repository: Annotated[AppRepository, Depends(AppRepository)]) -> App:
    return await app_repository.get_by_id(app_id) or await app_repository.insert(App(_id=app_id))


async def check_ip_not_blacklisted(app: Annotated[App, Depends(get_app)], ip: Annotated[str, Depends(get_ip)]) -> None:
    for system_info in app.blacklisted_system_infos:
        if system_info.ip_geolocation is None:
            continue

        if system_info.ip_geolocation['ip'] == ip:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


async def get_app_monitor(app_id: AppId, http_connection: HTTPConnection) -> AppMonitor:
    if not app_id in http_connection.app.state.app_monitors:
        http_connection.app.state.app_monitors[app_id] = AppMonitor(app_id)

    return http_connection.app.state.app_monitors[app_id]


def get_app_zip_path(app_id: AppId, release_type: ReleaseType | None = ReleaseType.LATEST) -> Path:
    file_name_suffix = '_old' if release_type is ReleaseType.OLD else ''
    path = config.apps_path / f'{config.app_names[app_id]}{file_name_suffix}.zip'

    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=config.file_not_found_message_error)

    return path


async def get_http_client_context(
    encrypted_body: Annotated[bytes, Body(media_type=config.bytes_media_type)],
    session: Annotated[aiohttp.ClientSession, Depends(get_http_session)],
    ip: Annotated[str, Depends(get_ip)]
) -> ClientContext:
    return await client_context_service.build_client_context(encrypted_body, session, ip)
