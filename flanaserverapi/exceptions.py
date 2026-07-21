class IncompleteUploadError(Exception):
    def __init__(self) -> None:
        super().__init__('Upload is incomplete')


class InvalidChunkError(Exception):
    def __init__(self) -> None:
        super().__init__('Invalid upload chunk')


class NotVideoFileError(Exception):
    def __init__(self) -> None:
        super().__init__('Not a video file')


class PayloadTooLargeError(Exception):
    def __init__(self, max_upload_size: int) -> None:
        super().__init__(f'Payload too large (max. {max_upload_size} bytes)')


class ThumbnailError(Exception):
    def __init__(self) -> None:
        super().__init__('Error generating thumbnail')


class UploadFinalizedError(Exception):
    def __init__(self) -> None:
        super().__init__('Upload is finalized')


class UploadNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__('Upload not found')
