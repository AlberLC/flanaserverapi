import mimetypes
import subprocess
import urllib.parse
from pathlib import Path

from config import config
from exceptions import ThumbnailError


def get_mime_type(file: str | Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(file))

    if not mime_type:
        mime_type = config.mime_types['bytes']

    return mime_type


def get_video_resolution(file_path: str | Path) -> tuple[int, int]:
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0:s=x',
        str(file_path)
    ]

    try:
        output = subprocess.check_output(cmd, text=True).strip()
        width, height = (int(size) for size in output.split('x'))
    except (ValueError, subprocess.CalledProcessError):
        return config.default_resolution
    else:
        return width, height


def get_video_thumbnail(file_path: str | Path) -> bytes:
    cmd = [
        'ffmpeg',
        '-i',
        str(file_path),
        '-vframes',
        '1',
        '-f',
        'image2pipe',
        '-vcodec',
        'png',
        'pipe:1'
    ]

    try:
        return subprocess.run(cmd, capture_output=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        raise ThumbnailError from e


def normalize_file_name(file_name: str) -> str:
    file_name_path = Path(file_name)
    return f'{replace_non_alpha_with_underscore(file_name_path.stem)}{file_name_path.suffix}'


def replace_non_alpha_with_underscore(text: str) -> str:
    characters: list[str] = []
    previous_was_underscore = False

    for character in urllib.parse.unquote(text):
        if character.isalpha():
            characters.append(character)
            previous_was_underscore = False
        elif not previous_was_underscore:
            characters.append('_')
            previous_was_underscore = True

    return ''.join(characters)
