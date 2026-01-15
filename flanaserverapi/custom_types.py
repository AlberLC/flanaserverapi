from typing import Literal

from config import config

# noinspection PyTypeHints
type AppId = Literal[*config.app_names]
