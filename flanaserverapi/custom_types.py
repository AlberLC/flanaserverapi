from typing import Literal

from config import config

# noinspection PyTypeHints
type AppId = Literal[*config.compressed_app_names]
