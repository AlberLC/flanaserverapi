import base64
import hashlib
import json
import secrets
from typing import Annotated, Any

from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse

from api.dependencies.http_dependencies import get_access_token_hash
from api.dependencies.repository_dependencies import get_repository
from api.schemas.create_upload_request import CreateUploadRequest
from api.schemas.create_upload_response import CreateUploadResponse
from config import config
from database.repositories.physical_file_repository import PhysicalFileRepository
from database.repositories.temporary_file_repository import TemporaryFileRepository
from database.repositories.virtual_file_repository import VirtualFileRepository
from services import file_service, upload_service
from utils import crypto_utils

router = APIRouter(prefix='/wedding', tags=['wedding'])


def _load_wedding_config(key: str) -> Any:
    if config.wedding_config_path.is_file():
        return json.loads(config.wedding_config_path.read_text()).get(key)


def _save_wedding_config(key: str, value: Any) -> None:
    if config.wedding_config_path.is_file():
        wedding_config = json.loads(config.wedding_config_path.read_text())
    else:
        wedding_config = {}

    wedding_config[key] = value

    config.wedding_config_path.write_text(json.dumps(wedding_config, ensure_ascii=False, indent=2))


def require_wedding_admin_session(wedding_admin_session: Annotated[str | None, Cookie()] = None) -> None:
    try:
        # noinspection bad-argument-type
        crypto_utils.verify(b'', base64.urlsafe_b64decode(wedding_admin_session))
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid admin session')


def require_wedding_code_session(wedding_code_session: Annotated[str | None, Cookie()] = None) -> None:
    if (code := _load_wedding_config('code')) is None:
        return

    try:
        # noinspection bad-argument-type
        crypto_utils.verify(hashlib.sha256(code.encode()).digest(), base64.urlsafe_b64decode(wedding_code_session))
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid code session')


def require_wedding_session(
    wedding_admin_session: Annotated[str | None, Cookie()] = None,
    wedding_code_session: Annotated[str | None, Cookie()] = None
) -> None:
    try:
        require_wedding_admin_session(wedding_admin_session)
    except HTTPException:
        require_wedding_code_session(wedding_code_session)


@router.post('/login', status_code=status.HTTP_204_NO_CONTENT)
async def wedding_admin_login(password: Annotated[str, Body()], response: Response) -> None:
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    if not secrets.compare_digest(password_hash, config.wedding_admin_password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid password')

    response.set_cookie(
        key=config.wedding_admin_session_cookie,
        value=base64.urlsafe_b64encode(crypto_utils.sign(b'')).decode(),
        max_age=86400
    )


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
async def wedding_admin_logout(response: Response) -> None:
    response.delete_cookie(key=config.wedding_admin_session_cookie)


@router.get('/qrcodes/{id}')
async def get_wedding_locked(id: int) -> FileResponse:
    return FileResponse(config.wedding_qrcode_paths[id])


@router.get('/locked')
async def get_wedding_locked() -> bool | None:
    return _load_wedding_config('lock')


@router.put('/locked', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_wedding_admin_session)])
async def set_wedding_locked(lock: Annotated[bool | None, Body()] = None) -> None:
    _save_wedding_config('lock', lock)


@router.get('/code', dependencies=[Depends(require_wedding_admin_session)])
async def get_wedding_code() -> str | None:
    return _load_wedding_config('code')


@router.put('/code', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_wedding_admin_session)])
async def set_wedding_code(code: Annotated[str | None, Body()] = None) -> None:
    _save_wedding_config('code', code)


@router.get('/code/configured')
async def is_wedding_code_configured() -> bool:
    return _load_wedding_config('code') is not None


@router.post('/verify-code', status_code=status.HTTP_204_NO_CONTENT)
async def verify_wedding_code(
    response: Response,
    code: Annotated[str | None, Body()] = None,
    wedding_code_session: Annotated[str | None, Cookie()] = None
) -> None:
    if (expected_code := _load_wedding_config('code')) is None:
        return

    try:
        require_wedding_code_session(wedding_code_session)
    except HTTPException:
        if code is None or not secrets.compare_digest(code, expected_code):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid code')

        response.set_cookie(
            key=config.wedding_code_session_cookie,
            value=base64.urlsafe_b64encode(crypto_utils.sign(hashlib.sha256(code.encode()).digest())).decode(),
            max_age=86400
        )


@router.get('/file-responses-limit')
async def get_wedding_file_responses_limit() -> int | None:
    return _load_wedding_config('file_responses_limit')


@router.put(
    '/file-responses-limit',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_wedding_admin_session)]
)
async def set_wedding_file_responses_limit(file_responses_limit: Annotated[int | None, Body()]) -> None:
    _save_wedding_config('file_responses_limit', file_responses_limit)


@router.get('/message')
async def get_wedding_message() -> str | None:
    return _load_wedding_config('message')


@router.put('/message', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_wedding_admin_session)])
async def set_wedding_message(message: Annotated[str | None, Body()] = None) -> None:
    _save_wedding_config('message', message)


@router.post('/uploads', status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_wedding_session)])
async def wedding_create_upload(
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


@router.delete(
    '/files/{file_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_wedding_admin_session)]
)
async def delete_wedding_file(
    file_id: str,
    access_token_hash: Annotated[str, Depends(get_access_token_hash)],
    physical_file_repository: Annotated[PhysicalFileRepository, Depends(get_repository(PhysicalFileRepository))],
    virtual_file_repository: Annotated[VirtualFileRepository, Depends(get_repository(VirtualFileRepository))]
) -> None:
    try:
        await file_service.delete_file(file_id, access_token_hash, physical_file_repository, virtual_file_repository)
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
