"""Weather NOAA gateway implementation for US weather data.

This gateway directly implements WeatherGateway interface for NOAA ISD data access.
Data source: NOAA Integrated Surface Database (ISD)
https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
"""

import logging
from typing import Dict, Tuple, List, Optional
from datetime import datetime, date, timedelta
import re

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.adapter.interfaces.clients.http_client_interface import HttpClientInterface
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway


# NOAA ISD 観測地点マッピング（緯度経度 → (USAF, WBAN, name)）
# アメリカ主要都市の観測所を定義
LOCATION_MAPPING: Dict[Tuple[float, float], Tuple[str, str, str, float, float]] = {
    # (latitude, longitude): (usaf, wban, name, actual_lat, actual_lon)
    
    # 東海岸
    (40.7128, -74.0060): ("725030", "14732", "LaGuardia Airport, NY", 40.7769, -73.8739),  # New York
    (42.3601, -71.0589): ("725090", "14739", "Boston Logan Airport, MA", 42.3606, -71.0096),  # Boston
    (38.9072, -77.0369): ("724050", "13743", "Washington Dulles Airport, DC", 38.9531, -77.4565),  # Washington DC
    (25.7617, -80.1918): ("722020", "12839", "Miami Airport, FL", 25.7932, -80.2906),  # Miami
    (33.7490, -84.3880): ("722190", "13874", "Atlanta Airport, GA", 33.6367, -84.4281),  # Atlanta
    
    # 中西部
    (41.8781, -87.6298): ("725300", "94846", "Chicago O'Hare Airport, IL", 41.9950, -87.9336),  # Chicago
    (39.7392, -104.9903): ("724699", "03017", "Denver Airport, CO", 39.8561, -104.6737),  # Denver
    (29.7604, -95.3698): ("722430", "12960", "Houston Bush Airport, TX", 29.9844, -95.3414),  # Houston
    (32.7767, -96.7970): ("722590", "03927", "Dallas Fort Worth Airport, TX", 32.8998, -97.0403),  # Dallas
    
    # 西海岸
    (34.0522, -118.2437): ("722950", "23174", "Los Angeles Airport, CA", 33.9381, -118.3889),  # Los Angeles
    (37.7749, -122.4194): ("724940", "23234", "San Francisco Airport, CA", 37.6213, -122.3790),  # San Francisco
    (47.6062, -122.3321): ("727930", "24233", "Seattle Tacoma Airport, WA", 47.4502, -122.3088),  # Seattle
    (45.5152, -122.6784): ("726980", "24229", "Portland Airport, OR", 45.5887, -122.5975),  # Portland
    (32.7157, -117.1611): ("722900", "23188", "San Diego Airport, CA", 32.7336, -117.1830),  # San Diego
    
    # その他主要都市
    (36.1699, -115.1398): ("723860", "23169", "Las Vegas Airport, NV", 36.0801, -115.1522),  # Las Vegas
    (33.4484, -112.0740): ("722780", "23183", "Phoenix Airport, AZ", 33.4342, -112.0116),  # Phoenix
    (30.2672, -97.7431): ("722540", "13904", "Austin Airport, TX", 30.1945, -97.6699),  # Austin
}


class WeatherNOAAGateway(WeatherGateway):
    """Gateway for fetching weather data from NOAA ISD.
    
    Directly implements WeatherGateway interface without intermediate layers.
    Uses NOAA Integrated Surface Database via HTTP access.
    """
    
    # NOAA ISD データアクセスURL
    BASE_URL = "https://www.ncei.noaa.gov/data/global-hourly/access"
    
    def __init__(self, http_client: HttpClientInterface):
        """Initialize NOAA weather gateway.
        
        Args:
            http_client: HTTP client for data access
        """
        self.http_client = http_client
        self.logger = logging.getLogger(__name__)
    
    async def get(self) -> List[WeatherData]:
        """Get weather data from configured source.
        
        Note: This method is not used for NOAA weather data.
        Use get_by_location_and_date_range() instead.
        
        Raises:
            NotImplementedError: NOAA requires location and date range parameters
        """
        raise NotImplementedError(
            "NOAA weather source requires location and date range. "
            "Use get_by_location_and_date_range() instead."
        )
    
    async def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create weather data at destination.
        
        Raises:
            NotImplementedError: Weather data creation not supported for NOAA source
        """
        raise NotImplementedError(
            "Weather data creation not supported for NOAA source"
        )
    
    async def get_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherDataWithLocationDTO:
        """Get weather forecast.
        
        Raises:
            NotImplementedError: NOAA ISD does not provide forecast data
        """
        raise NotImplementedError(
            "NOAA ISD does not provide forecast data. Use Open-Meteo API instead."
        )
    
    def _find_nearest_location(self, latitude: float, longitude: float) -> Tuple[str, str, str, float, float]:
        """Find the nearest NOAA observation station.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            
        Returns:
            Tuple of (usaf, wban, location_name, station_lat, station_lon)
            
        Raises:
            WeatherAPIError: If no suitable location found
        """
        min_distance = float('inf')
        nearest = None
        
        for (lat, lon), (usaf, wban, name, st_lat, st_lon) in LOCATION_MAPPING.items():
            # 簡易的な距離計算（緯度経度の差の二乗和）
            distance = ((latitude - lat) ** 2 + (longitude - lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest = (usaf, wban, name, st_lat, st_lon)
        
        if nearest is None:
            raise WeatherAPIError(
                f"No NOAA observation station found for location ({latitude}, {longitude})"
            )
        
        return nearest
    
    async def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
        """Get weather data from NOAA ISD.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            WeatherDataWithLocationDTO containing weather data and location
            
        Raises:
            WeatherAPIError: If data retrieval fails
            WeatherDataNotFoundError: If no data found
        """
        try:
            # Find nearest observation station
            usaf, wban, location_name, station_lat, station_lon = self._find_nearest_location(latitude, longitude)
            
            self.logger.info(
                f"Using NOAA station: {location_name} (USAF: {usaf}, WBAN: {wban}) "
                f"at ({station_lat}, {station_lon})"
            )
            
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
            
            # Collect data for each year in the range
            all_weather_data = []
            failed_years = []
            
            current_year = start.year
            end_year = end.year
            
            while current_year <= end_year:
                try:
                    # Build filename for this year
                    # Format: {USAF}-{WBAN}-{YEAR}.csv
                    filename = f"{usaf}-{wban}-{current_year}.csv"
                    url = f"{self.BASE_URL}/{current_year}/{filename}"
                    
                    self.logger.info(f"Fetching NOAA data from: {url}")
                    
                    # Fetch CSV data (as text)
                    response_text = await self._fetch_csv_text(url)
                    
                    # Parse CSV data
                    year_data = self._parse_noaa_csv(response_text, start_date, end_date)
                    all_weather_data.extend(year_data)
                    
                except Exception as e:
                    # Log failure but continue with other years
                    failed_years.append(current_year)
                    self.logger.warning(
                        f"Failed to fetch data for {current_year}: {e}. "
                        f"Continuing with available data."
                    )
                
                current_year += 1
            
            # If we got no data at all, raise error
            if not all_weather_data:
                raise WeatherDataNotFoundError(
                    f"No weather data found for location ({latitude}, {longitude}) "
                    f"from {start_date} to {end_date}. "
                    f"Station: {location_name}. "
                    f"Failed years: {failed_years if failed_years else 'None'}"
                )
            
            # Log partial success if any years failed
            if failed_years:
                self.logger.warning(
                    f"Partial data returned. Missing data for {len(failed_years)} year(s): {failed_years}"
                )
            
            # Group by day and calculate daily statistics
            daily_weather_data = self._aggregate_to_daily(all_weather_data)
            
            # Create location
            location = Location(
                latitude=station_lat,
                longitude=station_lon,
                elevation=None,  # ISD doesn't always provide elevation
                timezone="America/New_York"  # デフォルト（本来は座標から判定すべき）
            )
            
            return WeatherDataWithLocationDTO(
                weather_data_list=daily_weather_data,
                location=location
            )
            
        except WeatherAPIError:
            raise
        except Exception as e:
            raise WeatherAPIError(f"Failed to fetch NOAA data: {e}")
    
    async def _fetch_csv_text(self, url: str) -> str:
        """Fetch CSV text from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            CSV text content
            
        Raises:
            WeatherAPIError: If fetch fails
        """
        import requests
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise WeatherAPIError(f"Failed to fetch NOAA data from {url}: {e}")
    
    def _parse_noaa_csv(
        self,
        csv_text: str,
        start_date: str,
        end_date: str
    ) -> List[WeatherData]:
        """Parse NOAA ISD CSV data.
        
        Args:
            csv_text: CSV text content
            start_date: Filter start date (YYYY-MM-DD)
            end_date: Filter end date (YYYY-MM-DD)
            
        Returns:
            List of WeatherData entities (hourly)
        """
        import csv
        from io import StringIO
        
        weather_data_list = []
        
        # Parse date range for filtering
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        reader = csv.DictReader(StringIO(csv_text))
        
        for row in reader:
            try:
                # Parse date/time
                date_str = row.get('DATE', '')
                if not date_str:
                    continue
                
                # DATE format: 2024-01-15T12:00:00
                record_time = datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                
                # Filter by date range
                if record_time.date() < start_dt.date() or record_time.date() > end_dt.date():
                    continue
                
                # Extract temperature (TMP column: "+15.5,1" format)
                temp = self._parse_noaa_value(row.get('TMP', ''))
                
                # Extract precipitation (AA1 column for precipitation)
                precip = self._parse_noaa_value(row.get('AA1', ''), scale=10.0)  # Convert mm/10 to mm
                
                # Extract wind speed (WND column)
                wind_speed = self._parse_noaa_value(row.get('WND', ''))
                
                # Create WeatherData entity (hourly)
                weather_data = WeatherData(
                    time=record_time,
                    temperature_2m_max=temp,  # 時間データなので仮でmaxに入れる
                    temperature_2m_min=temp,  # 時間データなので仮でminに入れる
                    temperature_2m_mean=temp,
                    precipitation_sum=precip,
                    sunshine_duration=None,  # NOAA ISDには含まれない
                    wind_speed_10m=wind_speed,
                    weather_code=None,
                )
                
                weather_data_list.append(weather_data)
                
            except Exception as e:
                self.logger.warning(f"Failed to parse row: {e}")
                continue
        
        return weather_data_list
    
    def _parse_noaa_value(self, value_str: str, scale: float = 10.0) -> Optional[float]:
        """Parse NOAA value format.
        
        NOAA format: "+15.5,1" where first part is value*10, second is quality
        
        Args:
            value_str: Value string from NOAA CSV
            scale: Scale divisor (default 10.0)
            
        Returns:
            Parsed float value or None
        """
        if not value_str or value_str == '':
            return None
        
        try:
            # Split by comma
            parts = value_str.split(',')
            if len(parts) < 1:
                return None
            
            # Extract numeric part
            value_part = parts[0].strip()
            
            # Handle missing data indicators
            if value_part in ['+9999', '9999', '+999999', '999999']:
                return None
            
            # Convert to float and scale
            value = float(value_part) / scale
            
            return value
            
        except (ValueError, IndexError):
            return None
    
    def _aggregate_to_daily(self, hourly_data: List[WeatherData]) -> List[WeatherData]:
        """Aggregate hourly data to daily statistics.
        
        Args:
            hourly_data: List of hourly WeatherData
            
        Returns:
            List of daily WeatherData with min/max/mean
        """
        from collections import defaultdict
        
        # Group by date
        daily_groups = defaultdict(list)
        for data in hourly_data:
            date_key = data.time.date()
            daily_groups[date_key].append(data)
        
        daily_weather_data = []
        
        for date_key in sorted(daily_groups.keys()):
            day_records = daily_groups[date_key]
            
            # Calculate statistics
            temps = [r.temperature_2m_mean for r in day_records if r.temperature_2m_mean is not None]
            precips = [r.precipitation_sum for r in day_records if r.precipitation_sum is not None]
            winds = [r.wind_speed_10m for r in day_records if r.wind_speed_10m is not None]
            
            # Create daily weather data
            daily_data = WeatherData(
                time=datetime.combine(date_key, datetime.min.time()),
                temperature_2m_max=max(temps) if temps else None,
                temperature_2m_min=min(temps) if temps else None,
                temperature_2m_mean=sum(temps) / len(temps) if temps else None,
                precipitation_sum=sum(precips) if precips else None,
                sunshine_duration=None,
                wind_speed_10m=max(winds) if winds else None,
                weather_code=None,
            )
            
            daily_weather_data.append(daily_data)
        
        return daily_weather_data

