from fastapi import Request


def get_root_path(request: Request) -> str:
    return request.scope['path'].split('/', maxsplit=2)[1]
