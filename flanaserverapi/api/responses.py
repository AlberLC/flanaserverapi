from fastapi import status

from config import config

bytes_responses = {status.HTTP_200_OK: {'content': {config.mime_types['bytes']: {}}}}
zip_responses = {status.HTTP_200_OK: {'content': {config.mime_types['zip']: {}}}}
