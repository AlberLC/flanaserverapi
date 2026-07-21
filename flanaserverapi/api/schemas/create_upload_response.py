from pydantic import BaseModel


class CreateUploadResponse(BaseModel):
    id: str
    chunk_size: int
