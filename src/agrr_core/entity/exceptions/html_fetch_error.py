"""HTML fetch error exception."""

class HtmlFetchError(Exception):
    """Exception raised when HTML fetch or parsing fails."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

