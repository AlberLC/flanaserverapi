import datetime
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    api_host: str | None = None
    api_port: int | None = None
    subdomain: str | None = None

    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / '.env')


class DuckDNSSettings(AppSettings):
    duckdns_ip_updater_endpoint: str | None = None
    duckdns_ip_updater_endpoint_template: str = (
        'https://www.duckdns.org/update?domains={subdomain}&token={duckdns_token}&ip='
    )
    duckdns_ip_updater_error_message: str = 'Error updating IP'
    duckdns_ip_updater_sleep: float = datetime.timedelta(minutes=5).total_seconds()
    duckdns_token: str | None = None

    def model_post_init(self, _context: Any = None):
        self.duckdns_ip_updater_endpoint = self.duckdns_ip_updater_endpoint_template.format(
            subdomain=self.subdomain,
            duckdns_token=self.duckdns_token
        )


class PathSettings(AppSettings):
    audio_thumbnail_name: str = 'audio_thumbnail.jpg'
    default_thumbnail_name: str = 'default_thumbnail.webp'
    flanaarena_zip_name: str = 'FlanaArena.zip'
    flanacs_zip_name: str = 'FlanaCS.zip'
    flanatrigo_zip_name: str = 'FlanaTrigo.zip'

    root_path: Path = Path(__file__).parent

    resources_path: Path = root_path / 'resources'

    files_metadata_path: Path = resources_path / 'files_metadata.json'

    static_path: Path = root_path / 'static'

    files_path: Path = static_path / 'files'

    flanaarena_path: Path = static_path / 'flanaarena'
    flanaarena_zip_path: Path = flanaarena_path / flanaarena_zip_name

    flanacs_path: Path = static_path / 'flanacs'
    flanacs_zip_path: Path = flanacs_path / flanacs_zip_name
    flanacs_zip_path_old: Path = flanacs_path / 'FlanaCS_old.zip'

    flanatrigo_path: Path = static_path / 'flanatrigo'
    flanatrigo_zip_path: Path = flanatrigo_path / flanatrigo_zip_name
    flanatrigo_version_path: Path = flanatrigo_path / 'version.txt'


class Config(DuckDNSSettings, PathSettings):
    default_resolution: tuple[int, int] = (1280, 720)
    files_cleaner_sleep: float = datetime.timedelta(minutes=5).total_seconds()
    files_max_storage_size: int = 20_000_000_000
    open_graph_type_map: dict[str, str] = {'audio': 'music.song', 'image': 'image', 'video': 'video.other'}
    upload_max_size: int = 3_000_000_000


config = Config()
