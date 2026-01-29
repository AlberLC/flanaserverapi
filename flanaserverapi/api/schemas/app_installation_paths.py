from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

from api.serializers import to_raw_paths


class AppInstallationPaths(BaseModel):
    directory_paths: Annotated[list[Path], PlainSerializer(to_raw_paths)]
    compressed_paths: Annotated[list[Path], PlainSerializer(to_raw_paths)]
