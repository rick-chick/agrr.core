"""CSV service interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class CsvServiceInterface(ABC):
    """Interface for CSV download and parsing operations."""
    
    @abstractmethod
    async def download_csv(
        self,
        url: str,
        encoding: str = 'utf-8'
    ) -> pd.DataFrame:
        """
        Download and parse CSV data.
        
        Args:
            url: URL to download CSV from
            encoding: Character encoding of the CSV file
            
        Returns:
            DataFrame containing the parsed CSV data
            
        Raises:
            CsvDownloadError: If download or parsing fails
        """
        pass

