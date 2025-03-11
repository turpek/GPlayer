class InvalidFrameIdError(Exception):
    def __init__(self, message):
        self.message = message


class VideoBufferError(Exception):
    def __init__(self, message):
        self.message = message


class VideoOpenError(Exception):
    def __init__(self, message):
        self.message = message


class SectionError(Exception):
    def __init__(self, message):
        self.message = message


class SectionIdError(Exception):
    def __init__(self, message):
        self.message = message


class SimpleStackError(Exception):
    def __init__(self, message):
        self.message = message
