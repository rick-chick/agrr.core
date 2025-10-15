"""File service interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import Any


class FileServiceInterface(ABC):
    """Interface for basic file operations."""
    
    @abstractmethod
    async def read(self, file_path: str) -> str:
        """Read file content as string."""
        pass
    
    @abstractmethod
    async def write(self, content: Any, file_path: str) -> None:
        """Write content to file."""
        pass
    
    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass

