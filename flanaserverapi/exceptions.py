class NotVideoFileError(Exception):
    def __init__(self) -> None:
        super().__init__('Not a video file')


class PayloadTooLarge(Exception):
    def __init__(self, max_upload_size: int) -> None:
        super().__init__(f'Payload too large (max. {max_upload_size} bytes)')


class ThumbnailError(Exception):
    def __init__(self) -> None:
        super().__init__('Error generating thumbnail')
