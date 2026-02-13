from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from exceptions import PayloadTooLarge


class LimitUploadSizeMiddleware:
    def __init__(self, app: ASGIApp, max_upload_size: int) -> None:
        self.app = app
        self.max_upload_size = max_upload_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        content_length = request.headers.get('content-length')

        try:
            if content_length is not None:
                try:
                    length = int(content_length)
                except ValueError, TypeError:
                    pass
                else:
                    if length > self.max_upload_size:
                        raise PayloadTooLarge(self.max_upload_size)

            await self.app(scope, self._create_limited_receive(receive), send)
        except PayloadTooLarge as e:
            response = JSONResponse({'error': str(e)}, status.HTTP_413_CONTENT_TOO_LARGE)
            await response(scope, receive, send)

    def _create_limited_receive(self, receive: Receive) -> Receive:
        size = 0

        async def limited_receive() -> Message:
            nonlocal size

            message = await receive()

            if message['type'] == 'http.request':
                body = message.get('body') or b''
                size += len(body)

                if size > self.max_upload_size:
                    raise PayloadTooLarge(self.max_upload_size)

            return message

        return limited_receive
