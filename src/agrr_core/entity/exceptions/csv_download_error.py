"""CSV download error exception."""


class CsvDownloadError(Exception):
    """Exception raised when CSV download or parsing fails."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

