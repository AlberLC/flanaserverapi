from pydantic import BaseModel


class UploadState(BaseModel):
    chunk_size: int
    uploaded_chunks: list[int]
