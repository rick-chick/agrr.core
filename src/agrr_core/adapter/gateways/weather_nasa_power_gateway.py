"""Weather NASA POWER gateway implementation for global coverage.

This gateway uses NASA Prediction Of Worldwide Energy Resources (POWER) API
to fetch weather data from any location worldwide.

Data source: NASA POWER API
https://power.larc.nasa.gov/

Coverage: Global (any latitude/longitude)
Period: 1984 - present
Resolution: 0.5° × 0.625° grid (~50km)
API Limits: ~1000 requests/hour (estimated), no API key required
"""

import logging

from typing import Dict, Tuple, List, Optional
from datetime import datetime

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.adapter.interfaces.clients.http_client_interface import HttpClientInterface
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway

class WeatherNASAPowerGateway(WeatherGateway):
    """Gateway for fetching weather data from NASA POWER API.
    
    Features:
    - Global coverage (any latitude/longitude)
    - Grid-based data (0.5° × 0.625° resolution)
    - Satellite + ground observation fusion
    - No API key required
    - Free, unlimited use (with rate limiting)
    """
    
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    RATE_LIMIT_DELAY = 1.0  # 1秒待機（レート制限対策）
    
    def __init__(self, http_client: HttpClientInterface):
        """Initialize NASA POWER weather gateway.
        
        Args:
            http_client: HTTP client for API access
        """
        self.http_client = http_client
        self.logger = logging.getLogger(__name__)
        self._request_count = 0
    
    def get(self) -> List[WeatherData]:
        """Get weather data from configured source.
        
        Note: This method is not used for NASA POWER API.
        Use get_by_location_and_date_range() instead.
        
        Raises:
            NotImplementedError: NASA POWER requires location and date range parameters
        """
        raise NotImplementedError(
            "NASA POWER API requires location and date range. "
            "Use get_by_location_and_date_range() instead."
        )
    
    def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create weather data at destination.
        
        Raises:
            NotImplementedError: Weather data creation not supported for NASA POWER
        """
        raise NotImplementedError(
            "Weather data creation not supported for NASA POWER source"
        )
    
    def get_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherDataWithLocationDTO:
        """Get weather forecast.
        
        Raises:
            NotImplementedError: NASA POWER does not provide forecast data
        """
        raise NotImplementedError(
            "NASA POWER does not provide forecast data. Use Open-Meteo API instead."
        )
    
    def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
        """Get weather data from NASA POWER API.
        
        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            start_date: Start date in YYYY-MM-DD format (1984-01-01 onwards)
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            WeatherDataWithLocationDTO containing weather data and location
            
        Raises:
            WeatherAPIError: If data retrieval fails
            WeatherDataNotFoundError: If no data found
        """
        try:
            # Validate coordinates
            if not -90 <= latitude <= 90:
                raise WeatherAPIError(f"Invalid latitude: {latitude} (must be -90 to 90)")
            if not -180 <= longitude <= 180:
                raise WeatherAPIError(f"Invalid longitude: {longitude} (must be -180 to 180)")
            
            # Parse and validate date range
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError as e:
                raise WeatherAPIError(
                    f"Invalid date format. Expected YYYY-MM-DD, "
                    f"got start_date='{start_date}', end_date='{end_date}': {e}"
                )
            
            # Validate date order
            if start > end:
                raise WeatherAPIError(
                    f"start_date ({start_date}) must be before or equal to "
                    f"end_date ({end_date})"
                )
            
            # Check minimum date (NASA POWER starts from 1984-01-01)
            min_date = datetime(1984, 1, 1)
            if start < min_date:
                self.logger.warning(
                    f"Start date {start_date} is before NASA POWER minimum date "
                    f"1984-01-01. Data may be incomplete."
                )
            
            self.logger.info(
                f"Fetching NASA POWER data for ({latitude}, {longitude}) "
                f"from {start_date} to {end_date}"
            )
            
            # Build URL
            url = self._build_url(latitude, longitude, start_date, end_date)
            
            # Rate limiting (1秒待機)
            if self._request_count > 0:
                asyncio.sleep(self.RATE_LIMIT_DELAY)
            
            # Fetch data
            response_data = self._fetch_data(url)
            self._request_count += 1
            
            # Parse data
            weather_data_list = self._parse_nasa_power_data(response_data, start_date, end_date)
            
            if not weather_data_list:
                raise WeatherDataNotFoundError(
                    f"No weather data found for location ({latitude}, {longitude}) "
                    f"from {start_date} to {end_date}"
                )
            
            self.logger.info(
                f"Successfully fetched {len(weather_data_list)} daily records "
                f"from NASA POWER API"
            )
            
            # Create location
            location = Location(
                latitude=latitude,
                longitude=longitude,
                elevation=None,  # NASA POWER doesn't provide elevation in response
                timezone=None    # Grid-based data, timezone not specific
            )
            
            return WeatherDataWithLocationDTO(
                weather_data_list=weather_data_list,
                location=location
            )
            
        except WeatherAPIError:
            raise
        except WeatherDataNotFoundError:
            raise
        except Exception as e:
            raise WeatherAPIError(f"Failed to fetch NASA POWER data: {e}")
    
    def _build_url(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> str:
        """Build NASA POWER API URL.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Full URL for API request
        """
        # Convert date format: YYYY-MM-DD → YYYYMMDD
        start_fmt = start_date.replace("-", "")
        end_fmt = end_date.replace("-", "")
        
        # Parameters for agriculture
        params = [
            "T2M_MAX",      # Maximum temperature at 2m (°C)
            "T2M_MIN",      # Minimum temperature at 2m (°C)
            "T2M",          # Average temperature at 2m (°C)
            "PRECTOTCORR",  # Precipitation corrected (mm/day)
            "WS2M",         # Wind speed at 2m (m/s)
            "ALLSKY_SFC_SW_DWN"  # Solar radiation (MJ/m²/day)
        ]
        
        url = (
            f"{self.BASE_URL}?"
            f"parameters={','.join(params)}"
            f"&community=AG"  # Agriculture community
            f"&longitude={longitude}"
            f"&latitude={latitude}"
            f"&start={start_fmt}"
            f"&end={end_fmt}"
            f"&format=JSON"
        )
        
        return url
    
    def _fetch_data(self, url: str) -> dict:
        """Fetch data from NASA POWER API.
        
        Args:
            url: API URL
            
        Returns:
            JSON response as dictionary
            
        Raises:
            WeatherAPIError: If request fails
        """
        import requests
        
        try:
            response = requests.get(url, timeout=60)  # 長期データは時間がかかる可能性
            response.raise_for_status()
            
            # Check rate limit headers
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
            if rate_limit_remaining:
                self.logger.info(f"Rate limit remaining: {rate_limit_remaining}")
            
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                raise WeatherAPIError(f"NASA POWER API error: {data['error']}")
            
            return data
            
        except requests.RequestException as e:
            raise WeatherAPIError(f"Failed to fetch NASA POWER data from {url}: {e}")
        except ValueError as e:
            raise WeatherAPIError(f"Failed to parse NASA POWER JSON response: {e}")
    
    def _parse_nasa_power_data(
        self,
        data: dict,
        start_date: str,
        end_date: str
    ) -> List[WeatherData]:
        """Parse NASA POWER API response to WeatherData entities.
        
        NASA POWER response format:
        {
          "parameters": {
            "T2M_MAX": {
              "20000101": 25.5,
              "20000102": 26.3,
              ...
            },
            "T2M_MIN": {...},
            "T2M": {...},
            "PRECTOTCORR": {...}
          }
        }
        
        Args:
            data: JSON response from NASA POWER API
            start_date: Filter start date (YYYY-MM-DD)
            end_date: Filter end date (YYYY-MM-DD)
            
        Returns:
            List of WeatherData entities (sorted by date)
        """
        weather_data_dict = {}  # Dict[datetime, WeatherData] for deduplication
        
        # Parse date range for filtering
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Extract parameters (data is in properties.parameter)
        properties = data.get('properties', {})
        parameters = properties.get('parameter', {})
        
        if not parameters:
            self.logger.warning("No 'parameter' data in NASA POWER response")
            return []
        
        # Get all available dates from T2M (average temperature)
        t2m_data = parameters.get('T2M', {})
        if not t2m_data:
            self.logger.warning("No T2M (average temperature) data in response")
            return []
        
        # Get other parameters
        t2m_max_data = parameters.get('T2M_MAX', {})
        t2m_min_data = parameters.get('T2M_MIN', {})
        precip_data = parameters.get('PRECTOTCORR', {})
        wind_data = parameters.get('WS2M', {})
        solar_data = parameters.get('ALLSKY_SFC_SW_DWN', {})
        
        # Parse each date
        for date_str, temp_mean in t2m_data.items():
            try:
                # Skip metadata keys (units, longname, etc.)
                # Date keys are 8-digit strings (YYYYMMDD)
                if not (isinstance(date_str, str) and len(date_str) == 8 and date_str.isdigit()):
                    continue
                
                # Parse date: YYYYMMDD → datetime
                record_date = datetime.strptime(date_str, "%Y%m%d")
                
                # Filter by date range
                if record_date < start_dt or record_date > end_dt:
                    continue
                
                # Extract values (handle missing data: -999 means no data)
                temp_max = self._safe_value(t2m_max_data.get(date_str))
                temp_min = self._safe_value(t2m_min_data.get(date_str))
                temp_mean_val = self._safe_value(temp_mean)
                precipitation = self._safe_value(precip_data.get(date_str))
                wind_speed = self._safe_value(wind_data.get(date_str))
                solar_radiation = self._safe_value(solar_data.get(date_str))
                
                # Convert solar radiation to sunshine duration (approximation)
                # MJ/m²/day → hours of sunshine
                # Rough conversion: 1 hour of sunshine ≈ 3.6 MJ/m²
                sunshine_duration = None
                if solar_radiation is not None:
                    sunshine_hours = solar_radiation / 3.6
                    sunshine_duration = sunshine_hours * 3600  # hours → seconds
                
                # Skip if all temperature values are None
                if temp_mean_val is None and temp_max is None and temp_min is None:
                    continue
                
                # Create WeatherData entity
                weather_data = WeatherData(
                    time=record_date,
                    temperature_2m_max=temp_max,
                    temperature_2m_min=temp_min,
                    temperature_2m_mean=temp_mean_val,
                    precipitation_sum=precipitation,
                    sunshine_duration=sunshine_duration,
                    wind_speed_10m=wind_speed,
                    weather_code=None,  # NASA POWER doesn't provide weather code
                )
                
                weather_data_dict[record_date] = weather_data
                
            except Exception as e:
                self.logger.warning(f"Failed to parse date {date_str}: {e}")
                continue
        
        # Return sorted list
        return sorted(weather_data_dict.values(), key=lambda x: x.time)
    
    def _safe_value(self, value) -> Optional[float]:
        """Safely convert value to float, handling NASA POWER missing data indicators.
        
        NASA POWER uses -999 to indicate missing data.
        
        Args:
            value: Value from NASA POWER API
            
        Returns:
            Float value or None if missing/invalid
        """
        if value is None:
            return None
        
        try:
            float_val = float(value)
            
            # NASA POWER missing data indicator
            if float_val == -999 or float_val < -900:
                return None
            
            return float_val
            
        except (ValueError, TypeError):
            return None

