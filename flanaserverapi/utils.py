import mimetypes
import pathlib
import subprocess

from config import config


def get_mime_type(file_path: str | pathlib.Path) -> tuple[str, str]:
    mime_type, _ = mimetypes.guess_type(str(file_path))

    if not mime_type:
        mime_type = 'application/octet-stream'

    return mime_type, mime_type.split('/')[0]


def get_video_resolution(file_path: str | pathlib.Path) -> tuple[int, int]:
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
        return config.default_reslution
    else:
        return width, height


def get_video_thumbnail(file_path: str | pathlib.Path) -> bytes:
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
        proc = subprocess.run(cmd, capture_output=True, check=True)
        return proc.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError('Error generating thumbnail') from e
