"""File error exception."""

class FileError(Exception):
    """Exception raised for file-related errors."""
    
    def __init__(self, message: str, error_code: str = None):
        """Initialize file error exception."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "FILE_ERROR"
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        return f"{self.error_code}: {self.message}"
