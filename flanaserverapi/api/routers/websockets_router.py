from typing import Annotated

import aiohttp
import websockets
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from api.dependencies.app_dependencies import get_app_monitor
from api.dependencies.http_dependencies import get_http_session, get_ip
from config import config
from services import client_context_service, license_service
from services.app_monitor import AppMonitor

router = APIRouter(prefix='/ws', tags=['ws'])


@router.websocket('/{app_id}/shutdown')
async def wait_app_shutdown(
    app_monitor: Annotated[AppMonitor, Depends(get_app_monitor)],
    ip: Annotated[str, Depends(get_ip)],
    session: Annotated[aiohttp.ClientSession, Depends(get_http_session)],
    websocket: WebSocket
) -> None:
    try:
        await websocket.accept()

        client_context = await client_context_service.build_client_context(await websocket.receive_bytes(), ip, session)
        app_monitor.add_client()

        while True:
            app = await app_monitor.wait_app()

            if license_service.generate_license(app, client_context).features.disable:
                await websocket.send_text(config.shutdown_ws_message)
                break
    except WebSocketDisconnect, websockets.ConnectionClosedError:
        pass
    finally:
        app_monitor.remove_client()
