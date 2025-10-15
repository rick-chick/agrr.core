"""CSV service implementation for framework layer."""

import requests
import pandas as pd
from io import StringIO
from typing import Optional

from agrr_core.entity.exceptions.csv_download_error import CsvDownloadError
from agrr_core.adapter.interfaces.io.csv_service_interface import CsvServiceInterface


class CsvService(CsvServiceInterface):
    """CSV service for fetching CSV data from URLs."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize CSV service.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session: Optional[requests.Session] = requests.Session()
    
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
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Decode with specified encoding
            csv_text = response.content.decode(encoding)
            
            # Parse CSV
            df = pd.read_csv(StringIO(csv_text))
            
            return df
            
        except requests.RequestException as e:
            raise CsvDownloadError(f"Failed to download CSV from {url}: {e}")
        except UnicodeDecodeError as e:
            raise CsvDownloadError(f"Failed to decode CSV with encoding {encoding}: {e}")
        except pd.errors.ParserError as e:
            raise CsvDownloadError(f"Failed to parse CSV: {e}")
        except Exception as e:
            raise CsvDownloadError(f"Unexpected error while downloading CSV: {e}")
    
    def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            self.session.close()
            self.session = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor to ensure session cleanup."""
        self.close()

