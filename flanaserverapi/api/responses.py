import mimetypes

from fastapi import status

from config import config

app_responses = {status.HTTP_200_OK: {'content': {mimetypes.types_map[config.compressed_app_default_extension]: {}}}}
bytes_responses = {status.HTTP_200_OK: {'content': {mimetypes.types_map['.bin']: {}}}}
