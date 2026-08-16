from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse

from api.dependencies.http_dependencies import get_access_token_hash
from api.dependencies.repository_dependencies import get_repository
from api.schemas.create_upload_request import CreateUploadRequest
from api.schemas.create_upload_response import CreateUploadResponse
from api.schemas.upload_state import UploadState
from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.temporary_file_repository import TemporaryFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository
from exceptions import (
    IncompleteUploadError,
    InvalidChunkError,
    ThumbnailError,
    UploadFinalizedError,
    UploadNotFoundError
)
from services import upload_service

router = APIRouter(prefix='/uploads')


@router.get('/{upload_id}')
async def get_upload_state(
    upload_id: str,
    access_token_hash: Annotated[str, Depends(get_access_token_hash)],
    temporary_file_repository: Annotated[TemporaryFileRepository, Depends(get_repository(TemporaryFileRepository))]
) -> UploadState:
    try:
        return await upload_service.get_upload_state(upload_id, access_token_hash, temporary_file_repository)
    except UploadNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.post('', status_code=status.HTTP_201_CREATED)
async def create_upload(
    access_token_hash: Annotated[str, Depends(get_access_token_hash)],
    create_upload_request: CreateUploadRequest,
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(get_repository(PhysicalFileRepository))],
    temporary_file_repository: Annotated[TemporaryFileRepository, Depends(get_repository(TemporaryFileRepository))],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(get_repository(VirtualFileRepository))]
) -> CreateUploadResponse:
    return await upload_service.create_upload(
        access_token_hash,
        create_upload_request,
        physical_file_repository,
        temporary_file_repository,
        virtual_file_repository
    )


@router.post('/{upload_id}/complete')
async def complete_upload(
    upload_id: str,
    access_token_hash: Annotated[str, Depends(get_access_token_hash)],
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(get_repository(PhysicalFileRepository))],
    temporary_file_repository: Annotated[TemporaryFileRepository, Depends(get_repository(TemporaryFileRepository))],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(get_repository(VirtualFileRepository))]
) -> JSONResponse:
    try:
        virtual_file_response, was_created = await upload_service.complete_upload(
            upload_id,
            access_token_hash,
            physical_file_repository,
            temporary_file_repository,
            virtual_file_repository
        )
    except UploadNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except (IncompleteUploadError, UploadFinalizedError) as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    except ThumbnailError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

    return JSONResponse(
        virtual_file_response.model_dump(mode='json'),
        status.HTTP_201_CREATED if was_created else status.HTTP_200_OK
    )


@router.patch('/{upload_id}/chunks', status_code=status.HTTP_204_NO_CONTENT)
async def upload_chunk(
    upload_id: str,
    access_token_hash: Annotated[str, Depends(get_access_token_hash)],
    chunk_index: Annotated[int, Header()],
    chunk_checksum: Annotated[str, Header()],
    chunk_bytes: Annotated[bytes, Body(media_type='application/octet-stream')],
    temporary_file_repository: Annotated[TemporaryFileRepository, Depends(get_repository(TemporaryFileRepository))]
) -> None:
    try:
        await upload_service.process_chunk(
            upload_id,
            access_token_hash,
            chunk_index,
            chunk_checksum,
            chunk_bytes,
            temporary_file_repository
        )
    except UploadNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except InvalidChunkError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))


@router.delete('/{upload_id}', status_code=status.HTTP_204_NO_CONTENT)
async def cancel_upload(
    upload_id: str,
    access_token_hash: Annotated[str, Depends(get_access_token_hash)],
    temporary_file_repository: Annotated[TemporaryFileRepository, Depends(get_repository(TemporaryFileRepository))]
) -> None:
    try:
        await upload_service.cancel_upload(upload_id, access_token_hash, temporary_file_repository)
    except UploadNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except UploadFinalizedError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
