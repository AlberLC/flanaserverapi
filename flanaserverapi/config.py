import base64
import datetime
from pathlib import Path
from typing import Annotated

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    api_host: str | None = None
    api_port: int | None = None
    api_token: str | None = None
    subdomain: str | None = None

    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / '.env')


class DuckDNSSettings(AppSettings):
    duckdns_ip_updater_endpoint: str = 'https://www.duckdns.org/update'
    duckdns_ip_updater_error_message: str = 'Error updating IP'
    duckdns_ip_updater_sleep: float = datetime.timedelta(minutes=5).total_seconds()
    duckdns_key: str | None = None


class IpGeolocationSettings(AppSettings):
    geojs_endpoint: str = 'https://get.geojs.io/v1/ip/geo.json'
    ip_geolocation_endpoint: str = 'https://api.ipgeolocation.io/v2/ipgeo'
    ip_geolocation_key: str | None = None


class MongoSettings(AppSettings):
    collections: dict[str, dict] = {
        'app': {
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['_id'],
                    'properties': {
                        '_id': {'bsonType': 'string'},
                        'version': {'bsonType': ['null', 'string'], 'pattern': r'^\d+\.\d+\.\d+$'}
                    }
                }
            }
        }
    }
    database_name: str = 'flanaserverapi'
    indexes: dict[str, list[dict]] = {
        'cached_ip_geolocation': [
            {
                'name': 'created_at_1',
                'keys': 'created_at',
                'expireAfterSeconds': datetime.timedelta(days=1).total_seconds()
            }
        ],
        'file_info': [
            {
                'name': 'created_at_1',
                'keys': 'created_at'
            },
            {
                'name': 'file_name_1',
                'keys': 'file_name',
                'unique': True
            }
        ]
    }
    mongo_username: str | None = None
    mongo_password: str | None = None


class PathSettings(AppSettings):
    audio_thumbnail_name: str = 'audio_thumbnail.jpg'
    default_thumbnail_name: str = 'default_thumbnail.webp'

    root_path: Path = Path(__file__).parent

    resources_path: Path = root_path / 'resources'

    images_path: Path = resources_path / 'images'
    audio_thumbnail_path: Path = images_path / audio_thumbnail_name
    default_thumbnail_path: Path = images_path / default_thumbnail_name

    storage_path: Path = root_path / 'storage'

    apps_path: Path = storage_path / 'apps'

    files_path: Path = storage_path / 'files'

    static_path: Path = storage_path / 'static'
    static_images_path: Path = static_path / 'images'
    static_audio_thumbnail_path: Path = static_images_path / audio_thumbnail_name
    static_default_thumbnail_path: Path = static_images_path / default_thumbnail_name


class Config(DuckDNSSettings, IpGeolocationSettings, MongoSettings, PathSettings):
    app_monitor_sleep: float = datetime.timedelta(seconds=1).total_seconds()
    bytes_media_type: str = 'application/octet-stream'
    client_connection_not_found_message_error: str = 'ClientConnection not found'
    compressed_app_names: dict[str, dict[str, str]] = {
        'flanaarena': {'stem': 'FlanaArena', 'suffix': '.zip'},
        'flanacs': {'stem': 'FlanaCS', 'suffix': '.zip'},
        'flanatrigo': {'stem': 'FlanaTrigo', 'suffix': '.zip'}
    }
    default_resolution: tuple[int, int] = (1280, 720)
    document_not_found_message_error: str = 'Document not found'
    file_not_found_message_error: str = 'File not found'
    files_cleaner_sleep: float = datetime.timedelta(minutes=5).total_seconds()
    files_max_storage_size: int = 20_000_000_000
    max_client_connections: int = 1000
    open_graph_type_map: dict[str, str] = {'audio': 'music.song', 'image': 'image', 'video': 'video.other'}
    private_key: Annotated[bytes, BeforeValidator(base64.b64decode)] | None = None
    shutdown_ws_message: str = 'shutdown'
    symmetric_key: Annotated[bytes, BeforeValidator(base64.b64decode)] | None = None
    system_info_identifying_attributes: tuple[str, ...] = ('username', 'hostname', 'mac_address', 'ip_geolocation')
    upload_max_size: int = 3_000_000_000


config = Config()
