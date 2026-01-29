from pydantic import BaseModel

from api.schemas.system_info import SystemInfo


class ClientContext(BaseModel):
    system_info: SystemInfo
    client_code: str | None = None
