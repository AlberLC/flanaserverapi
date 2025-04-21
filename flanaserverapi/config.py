from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    api_host: str | None = None
    api_port: int | None = None
    static_path: Path = Path('static')
    flanacs_path: Path = static_path / 'flanacs'
    flanatrigo_path: Path = static_path / 'flanatrigo'
    flanacs_zip_name: str = 'FlanaCS.zip'
    flanacs_zip_path: Path = flanacs_path / 'FlanaCS.zip'
    flanatrigo_zip_name: str = 'FlanaTrigo.zip'
    flanatrigo_zip_path: Path = flanatrigo_path / 'FlanaTrigo.zip'
    flanatrigo_version_path: Path = flanatrigo_path / 'version.txt'

    model_config = SettingsConfigDict(env_file='../.env')


config = Config()
