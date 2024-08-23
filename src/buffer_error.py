class VideoBufferError(Exception):
    def __init__(self, message):
        self.message = message


class VideoOpenError(Exception):
    def __init__(self, message):
        self.message = message
