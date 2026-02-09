import json
from pathlib import Path
from typing import Annotated

import aiohttp
from bson import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, PlainTextResponse, Response

from api.dependencies.app_dependencies import (check_ip_not_blacklisted, get_app, get_app_compressed_path, get_app_monitor, get_http_client_context)
from api.dependencies.http_dependencies import get_http_session, get_ip
from api.schemas.app import App
from api.schemas.client_connection import ClientConnection
from api.schemas.client_context import ClientContext
from config import config
from custom_types import AppId
from database.repositories.client_connection_repository import ClientConnectionRepository
from services import client_context_service, license_service
from services.app_monitor import AppMonitor
from utils import crypto, encoding

router = APIRouter(prefix='/{app_id}', tags=['apps'])


@router.get('/download', dependencies=[Depends(check_ip_not_blacklisted)])
@router.get('/download/{release_type}', dependencies=[Depends(check_ip_not_blacklisted)])
async def download(compressed_path: Annotated[Path, Depends(get_app_compressed_path)]) -> FileResponse:
    return FileResponse(compressed_path, filename=compressed_path.name)


@router.get('/version')
async def get_version(app: Annotated[App, Depends(get_app)]) -> PlainTextResponse:
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=config.document_not_found_message_error)

    if not app.version:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    return PlainTextResponse(app.version)


@router.patch('/installation_paths', include_in_schema=False)
async def register_installation_paths(
    encrypted_body: Annotated[bytes, Body(media_type=config.bytes_media_type)],
    client_connection_repository: Annotated[ClientConnectionRepository, Depends(ClientConnectionRepository)]
) -> Response:
    body = json.loads(crypto.decrypt(encrypted_body))
    client_connection_id = body['client_connection_id']

    if not (client_connection := await client_connection_repository.get_by_id(ObjectId(client_connection_id))):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=config.client_connection_not_found_message_error
        )

    client_connection.app_installation_paths.directory_paths.extend(
        Path(raw_path) for raw_path in body['directory_paths']
    )
    client_connection.app_installation_paths.compressed_paths.extend(
        Path(raw_path) for raw_path in body['compressed_paths']
    )
    await client_connection_repository.update(client_connection)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/license', include_in_schema=False)
async def get_license(
    app_id: AppId,
    client_context: Annotated[ClientContext, Depends(get_http_client_context)],
    app: Annotated[App, Depends(get_app)],
    client_connection_repository: Annotated[ClientConnectionRepository, Depends(ClientConnectionRepository)]
) -> dict[str, str]:
    client_connection = await client_connection_repository.insert(
        ClientConnection(app_id=app_id, system_info=client_context.system_info),
        limit=config.max_client_connections
    )

    license_ = license_service.generate_license(app, client_context)
    license_data = license_.model_dump_json()
    encoded_license_data = license_data.encode()
    encrypted_license = crypto.encrypt(
        json.dumps((license_data, crypto.sign(encoded_license_data)), default=encoding.bytes_to_base64).encode()
    )

    return {
        'client_connection_id': str(client_connection.id),
        'encrypted_license': encoding.bytes_to_base64(encrypted_license)
    }


@router.websocket('/ws/shutdown')
async def wait_shutdown(
    websocket: WebSocket,
    session: Annotated[aiohttp.ClientSession, Depends(get_http_session)],
    ip: Annotated[str, Depends(get_ip)],
    app_monitor: Annotated[AppMonitor, Depends(get_app_monitor)]
) -> None:
    try:
        await websocket.accept()

        client_context = await client_context_service.build_client_context(await websocket.receive_bytes(), session, ip)
        app_monitor.add_client()

        while True:
            app = await app_monitor.wait_app()

            if license_service.generate_license(app, client_context).features.disable:
                await websocket.send_text(config.shutdown_ws_message)
                break
    except WebSocketDisconnect:
        pass
    finally:
        app_monitor.remove_client()
