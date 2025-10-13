"""JMA (Japan Meteorological Agency) weather repository implementation."""

import logging
from typing import Dict, Tuple, List, Optional
from datetime import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.entity.exceptions.html_fetch_error import HtmlFetchError
from agrr_core.adapter.interfaces.html_table_fetch_interface import HtmlTableFetchInterface
from agrr_core.adapter.interfaces.html_table_structures import HtmlTable, TableRow
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO


# 主要都市の気象庁観測地点マッピング（緯度経度 → (都道府県番号, 地点番号)）
LOCATION_MAPPING: Dict[Tuple[float, float], Tuple[int, int, str]] = {
    # (latitude, longitude): (prec_no, block_no, name)
    (35.6895, 139.6917): (44, 47662, "東京"),  # 東京
    (43.0642, 141.3469): (14, 47412, "札幌"),  # 札幌
    (38.2682, 140.8694): (34, 47590, "仙台"),  # 仙台
    (36.5614, 139.8833): (41, 47615, "前橋"),  # 前橋
    (35.4439, 139.6380): (46, 46106, "横浜"),  # 横浜
    (36.6519, 138.1881): (48, 47610, "長野"),  # 長野
    (35.1802, 136.9066): (51, 47636, "名古屋"),  # 名古屋
    (34.6937, 135.5023): (62, 47772, "大阪"),  # 大阪
    (34.3853, 132.4553): (66, 47765, "広島"),  # 広島
    (33.5904, 130.4017): (82, 47807, "福岡"),  # 福岡
    (26.2124, 127.6809): (91, 47936, "那覇"),  # 那覇
}


class WeatherJMARepository:
    """Repository for fetching weather data from JMA (Japan Meteorological Agency)."""
    
    BASE_URL = "https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php"
    
    def __init__(self, html_table_fetcher: HtmlTableFetchInterface):
        """
        Initialize JMA weather repository.
        
        Args:
            html_table_fetcher: HTML table fetch service
        """
        self.html_table_fetcher = html_table_fetcher
        self.logger = logging.getLogger(__name__)
    
    def _find_nearest_location(self, latitude: float, longitude: float) -> Tuple[int, int, str]:
        """
        Find the nearest JMA observation station.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            
        Returns:
            Tuple of (prec_no, block_no, location_name)
            
        Raises:
            WeatherAPIError: If no suitable location found
        """
        # 簡易的な最近傍探索（実際には距離計算が必要）
        min_distance = float('inf')
        nearest = None
        
        for (lat, lon), (prec_no, block_no, name) in LOCATION_MAPPING.items():
            distance = ((latitude - lat) ** 2 + (longitude - lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest = (prec_no, block_no, name)
        
        if nearest is None:
            raise WeatherAPIError(
                f"No JMA observation station found for location ({latitude}, {longitude})"
            )
        
        return nearest
    
    async def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
        """
        Get weather data from JMA.
        
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
            prec_no, block_no, location_name = self._find_nearest_location(latitude, longitude)
            
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
            
            # Collect data for each month in the range
            all_weather_data = []
            
            # Start from the first day of the start month
            current = start.replace(day=1)
            end_month = end.replace(day=1)
            
            while current <= end_month:
                # Build URL for this month
                url = self._build_url(prec_no, block_no, current.year, current.month)
                
                # Fetch HTML tables
                tables = await self.html_table_fetcher.get(url)
                
                # Find data table (id="tablefix1")
                data_table = self._find_data_table(tables)
                
                # Convert to WeatherData entities
                weather_data_list = self._parse_jma_table(data_table, start_date, end_date, current.year, current.month)
                all_weather_data.extend(weather_data_list)
                
                # Move to next month using relativedelta (handles month-end correctly)
                current = current + relativedelta(months=1)
            
            if not all_weather_data:
                raise WeatherDataNotFoundError(
                    f"No weather data found for location ({latitude}, {longitude}) "
                    f"from {start_date} to {end_date}"
                )
            
            # Create location
            location = Location(
                latitude=latitude,
                longitude=longitude,
                elevation=None,  # JMA doesn't provide elevation in CSV
                timezone="Asia/Tokyo"
            )
            
            return WeatherDataWithLocationDTO(
                weather_data_list=all_weather_data,
                location=location
            )
            
        except HtmlFetchError as e:
            raise WeatherAPIError(f"Failed to fetch JMA data: {e}")
        except (KeyError, ValueError, IndexError) as e:
            raise WeatherAPIError(f"Invalid JMA data format: {e}")
    
    def _build_url(self, prec_no: int, block_no: int, year: int, month: int) -> str:
        """
        Build JMA data URL.
        
        Args:
            prec_no: Prefecture number
            block_no: Block number
            year: Year
            month: Month
            
        Returns:
            Full URL for CSV download
        """
        return (
            f"{self.BASE_URL}?"
            f"prec_no={prec_no}&"
            f"block_no={block_no}&"
            f"year={year}&"
            f"month={month}&"
            f"day=&"
            f"view="
        )
    
    def _find_data_table(self, tables: List[HtmlTable]) -> HtmlTable:
        """
        データテーブル（id="tablefix1"）を見つける
        
        Args:
            tables: 全テーブルのリスト
            
        Returns:
            HtmlTable: データテーブル
            
        Raises:
            WeatherAPIError: データテーブルが見つからない場合
        """
        # id="tablefix1"を探す
        for table in tables:
            if table.table_id == 'tablefix1':
                return table
        
        # フォールバック: 最も行数が多いテーブル
        if tables:
            data_table = max(tables, key=lambda t: len(t.rows))
            if len(data_table.rows) > 0:
                return data_table
        
        raise WeatherAPIError("No data table found in JMA response")
    
    def _parse_jma_table(
        self,
        table: HtmlTable,
        start_date: str,
        end_date: str,
        year: int,
        month: int
    ) -> List[WeatherData]:
        """
        Parse JMA HTML table to WeatherData entities.
        
        テーブル構造（実データより）:
        - cells[0]: 日
        - cells[3]: 降水量合計(mm)
        - cells[6]: 平均気温(℃)
        - cells[7]: 最高気温(℃)
        - cells[8]: 最低気温(℃)
        - cells[16]: 日照時間(h)
        - cells[10]: 平均風速(m/s)
        - cells[12]: 最大風速・風速(m/s)
        
        Args:
            table: HtmlTable from JMA
            start_date: Filter start date (YYYY-MM-DD)
            end_date: Filter end date (YYYY-MM-DD)
            year: Year of the data
            month: Month of the data
            
        Returns:
            List of WeatherData entities
        """
        weather_data_list = []
        skipped_count = 0
        
        # Parse date range for filtering
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        for row in table.rows:
            try:
                # セル数が少ない場合はスキップ
                if len(row.cells) < 17:
                    continue
                
                # 日付を構築
                day_str = row.cells[0].strip()
                if not day_str or not day_str.isdigit():
                    continue
                
                day = int(day_str)
                record_date = datetime(year, month, day)
                
                # Filter by date range
                if record_date < start_dt or record_date > end_dt:
                    continue
                
                # Extract data from cells
                # cells[3]: 降水量合計
                # cells[6]: 平均気温
                # cells[7]: 最高気温
                # cells[8]: 最低気温
                # cells[16]: 日照時間(h)
                # cells[10]: 平均風速
                # cells[12]: 最大風速
                
                precipitation = self._safe_float(row.cells[3])
                temp_mean = self._safe_float(row.cells[6])
                temp_max = self._safe_float(row.cells[7])
                temp_min = self._safe_float(row.cells[8])
                
                # 日照時間（時間 → 秒に変換）
                sunshine_hours = self._safe_float(row.cells[16] if len(row.cells) > 16 else None)
                sunshine_duration = sunshine_hours * 3600 if sunshine_hours is not None else None
                
                # 風速（最大優先、なければ平均）
                wind_speed_max = self._safe_float(row.cells[12] if len(row.cells) > 12 else None)
                wind_speed_avg = self._safe_float(row.cells[10] if len(row.cells) > 10 else None)
                wind_speed = wind_speed_max if wind_speed_max is not None else wind_speed_avg
                
                # Create WeatherData entity
                weather_data = WeatherData(
                    time=record_date,
                    temperature_2m_max=temp_max,
                    temperature_2m_min=temp_min,
                    temperature_2m_mean=temp_mean,
                    precipitation_sum=precipitation,
                    sunshine_duration=sunshine_duration,
                    wind_speed_10m=wind_speed,
                    weather_code=None,  # JMA doesn't provide weather code
                )
                
                # Validate weather data before adding
                date_str = f"{year}-{month:02d}-{day:02d}"
                if self._validate_weather_data(weather_data, date_str):
                    weather_data_list.append(weather_data)
                else:
                    skipped_count += 1
                
            except Exception as e:
                # Skip problematic rows but continue processing
                day_info = row.cells[0] if row.cells else 'N/A'
                self.logger.warning(
                    f"Failed to parse row at day {day_info}: {e}. "
                    f"Cells: {row.cells[:5] if len(row.cells) >= 5 else row.cells}"
                )
                continue
        
        # Log skipped records
        if skipped_count > 0:
            self.logger.info(f"Skipped {skipped_count} invalid weather records due to data quality issues")
        
        return weather_data_list
    
    def _safe_float(self, value) -> Optional[float]:
        """
        Safely convert value to float.
        
        Args:
            value: Value to convert
            
        Returns:
            Float value or None if conversion fails
        """
        if value is None:
            return None
        
        # Check if it's a string
        if isinstance(value, str):
            value = value.strip()
            if not value or value == '--' or value == '×':
                return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _validate_weather_data(self, data: WeatherData, date_str: str = "") -> bool:
        """
        Validate weather data ranges.
        
        Args:
            data: WeatherData to validate
            date_str: Date string for logging
            
        Returns:
            True if valid, False if invalid
        """
        # Temperature range check (Japan realistic range)
        if data.temperature_2m_max is not None:
            if not -50 <= data.temperature_2m_max <= 50:
                self.logger.warning(
                    f"[{date_str}] Suspicious max temp: {data.temperature_2m_max}°C"
                )
                return False
        
        if data.temperature_2m_min is not None:
            if not -50 <= data.temperature_2m_min <= 50:
                self.logger.warning(
                    f"[{date_str}] Suspicious min temp: {data.temperature_2m_min}°C"
                )
                return False
        
        # Temperature inversion check
        if (data.temperature_2m_max is not None and 
            data.temperature_2m_min is not None):
            if data.temperature_2m_max < data.temperature_2m_min:
                self.logger.warning(
                    f"[{date_str}] Temperature inversion: "
                    f"max={data.temperature_2m_max}°C < min={data.temperature_2m_min}°C"
                )
                return False
        
        # Precipitation check
        if data.precipitation_sum is not None:
            if data.precipitation_sum < 0:
                self.logger.warning(
                    f"[{date_str}] Negative precipitation: {data.precipitation_sum}mm"
                )
                return False
            if data.precipitation_sum > 1000:  # Extreme but possible
                self.logger.warning(
                    f"[{date_str}] Extreme precipitation: {data.precipitation_sum}mm"
                )
        
        # Sunshine duration check
        if data.sunshine_duration is not None:
            if data.sunshine_duration < 0:
                self.logger.warning(
                    f"[{date_str}] Negative sunshine: {data.sunshine_duration}s"
                )
                return False
            if data.sunshine_duration > 24 * 3600:
                self.logger.warning(
                    f"[{date_str}] Sunshine over 24h: {data.sunshine_duration}s"
                )
                return False
        
        return True

