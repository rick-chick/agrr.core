"""File repository implementation for framework layer."""

from agrr_core.adapter.interfaces.file_repository_interface import FileRepositoryInterface


class FileRepository(FileRepositoryInterface):
    """Implementation of file repository interface."""
    
    def __init__(self):
        """Initialize file repository implementation."""
        pass
    
    async def read(self, file_path: str) -> str:
        """Read file content as string."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            from agrr_core.entity.exceptions.file_error import FileError
            raise FileError(f"Failed to read file {file_path}: {e}")
    
    async def write(self, content: str, file_path: str) -> None:
        """Write content to file."""
        try:
            from pathlib import Path
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
        except Exception as e:
            from agrr_core.entity.exceptions.file_error import FileError
            raise FileError(f"Failed to write file {file_path}: {e}")
    
    def exists(self, file_path: str) -> bool:
        """Check if file exists."""
        try:
            from pathlib import Path
            path = Path(file_path)
            return path.exists() and path.is_file()
        except Exception:
            return False
