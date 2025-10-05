"""HTTP service implementation for framework layer."""

import requests
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.adapter.interfaces.http_service_interface import HttpServiceInterface


class HttpClient(HttpServiceInterface):
    """Generic HTTP client for API requests."""
    
    def __init__(self, base_url: str = "", timeout: int = 30):
        """Initialize HTTP client."""
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        try:
            url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise WeatherAPIError(f"HTTP request failed: {e}")
        except Exception as e:
            raise WeatherAPIError(f"Failed to process HTTP response: {e}")
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request."""
        try:
            url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise WeatherAPIError(f"HTTP request failed: {e}")
        except Exception as e:
            raise WeatherAPIError(f"Failed to process HTTP response: {e}")
    
    def set_header(self, key: str, value: str) -> None:
        """Set HTTP header."""
        self.session.headers[key] = value
    
    def set_headers(self, headers: Dict[str, str]) -> None:
        """Set multiple HTTP headers."""
        self.session.headers.update(headers)
    
    def close(self) -> None:
        """Close HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
