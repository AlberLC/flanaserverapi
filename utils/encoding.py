import base64


def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode()
