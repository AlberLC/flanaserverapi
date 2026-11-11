import mimetypes

from fastapi import status
from pydantic import BaseModel


def get_binary_or_model_request_schema(model: type[BaseModel]) -> dict:
    return {
        'requestBody': {
            'content': {'application/octet-stream': {}, 'application/json': {'schema': model.model_json_schema()}}
        }
    }


def get_response_schema(extension: str) -> dict:
    return {status.HTTP_200_OK: {'content': {mimetypes.types_map[extension]: {}}}}
