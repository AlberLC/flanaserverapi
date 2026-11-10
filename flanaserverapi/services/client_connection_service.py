from config import config
from custom_types import AppId
from database.repositories.client_connection_repository import ClientConnectionRepository
from models.client_connections import ClientConnection
from models.system_info import SystemInfo


async def register_client_connection(
    app_id: AppId,
    system_info: SystemInfo,
    client_connection_repository: ClientConnectionRepository
) -> ClientConnection:
    client_connection = ClientConnection(app_id=app_id, system_info=system_info)

    await client_connection_repository.insert_one(
        client_connection,
        max_documents=config.max_client_connections,
        max_documents_sort=('date',)
    )

    return client_connection
