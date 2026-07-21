from pydantic import BaseModel


class CreateUploadRequest(BaseModel):
    file_name: str
    file_size: int
    file_mime_type: str
    file_expires_in: int | None = None
