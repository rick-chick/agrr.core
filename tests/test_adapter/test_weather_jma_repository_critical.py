"""Critical test cases for Weather JMA Repository.

These tests expose issues that must be fixed before production deployment.
Tests marked with @pytest.mark.xfail are expected to fail until corresponding
fixes are implemented.
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
import asyncio

from agrr_core.adapter.repositories.weather_jma_repository import WeatherJMARepository
from agrr_core.adapter.interfaces.html_table_fetch_interface import HtmlTableFetchInterface
from agrr_core.adapter.interfaces.html_table_structures import HtmlTable, TableRow
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.entity.exceptions.html_fetch_error import HtmlFetchError


def create_html_table_from_data(year, month, data_rows):
    """
    Helper function to create HtmlTable from data rows.
    
    Args:
        year: Year
        month: Month
        data_rows: List of tuples (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
    """
    rows = []
    for row_data in data_rows:
        day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max = row_data
        # セル構造: [日, 気圧現地, 気圧海面, 降水量, 降水量1h, 降水量10m, 
        #           平均気温, 最高気温, 最低気温, 湿度平均, 湿度最小, 平均風速, 風向, 最大風速, ...]
        cells = [
            str(day),  # 0: 日
            '1013.0',  # 1: 気圧現地
            '1023.0',  # 2: 気圧海面
            str(precip) if precip is not None else '',  # 3: 降水量合計
            '0.0',  # 4: 降水量1h
            '0.0',  # 5: 降水量10m
            str(temp_mean) if temp_mean is not None else '',  # 6: 平均気温
            str(temp_max) if temp_max is not None else '',  # 7: 最高気温
            str(temp_min) if temp_min is not None else '',  # 8: 最低気温
            '60',  # 9: 湿度平均
            '50',  # 10: 湿度最小
            str(wind_avg) if wind_avg is not None else '',  # 11: 平均風速 (m/s)
            str(wind_max) if wind_max is not None else '',  # 12: 最大風速 (m/s)
            '北',  # 13: 風向
            '10.0',  # 14: 最大風速・風速
            '0',  # 15: 最大瞬間風速・風速
            str(sunshine_h) if sunshine_h is not None else '',  # 16: 日照時間(h)
            '0.0',  # 17: 降雪
            '0.0',  # 18: 積雪
            '--',  # 19: 天気
            '--',  # 20: 雲量
        ]
        rows.append(TableRow(cells=cells))
    
    return HtmlTable(
        headers=[],  # ヘッダーは不要
        rows=rows,
        table_id='tablefix1'
    )


class TestWeatherJMARepositoryCritical:
    """Critical test cases that must pass before production."""
    
    @pytest.fixture
    def mock_html_fetcher(self):
        """Create mock HTML table fetcher."""
        service = AsyncMock(spec=HtmlTableFetchInterface)
        return service
    
    @pytest.fixture
    def repository(self, mock_html_fetcher):
        """Create repository instance."""
        return WeatherJMARepository(mock_html_fetcher)
    
    @pytest.fixture
    def valid_html_table(self):
        """Create valid JMA HTML table."""
        data_rows = [
            # (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
            (1, 0.0, 6.4, 10.5, 2.3, 5.2, 3.0, 3.5),
            (2, 2.5, 7.2, 11.2, 3.1, 3.1, 3.8, 4.2),
        ]
        return create_html_table_from_data(2024, 1, data_rows)
    
    # ========================================
    # Test 1: Invalid Date Format
    # ========================================
    @pytest.mark.asyncio
    async def test_invalid_date_format(self, repository, mock_html_fetcher):
        """Test that invalid date format raises clear error."""
        mock_html_fetcher.get.return_value = []
        
        with pytest.raises(WeatherAPIError) as exc_info:
            await repository.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024/01/01',  # Wrong format (should be YYYY-MM-DD)
                end_date='2024-01-31'
            )
        
        assert 'Invalid date format' in str(exc_info.value)
        assert 'YYYY-MM-DD' in str(exc_info.value)
    
    # ========================================
    # Test 2: Start Date After End Date
    # ========================================
    @pytest.mark.asyncio
    async def test_start_date_after_end_date(self, repository, mock_html_fetcher):
        """Test that start_date > end_date raises error."""
        mock_html_fetcher.get.return_value = []
        
        with pytest.raises(WeatherAPIError) as exc_info:
            await repository.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024-12-31',
                end_date='2024-01-01'
            )
        
        assert 'start_date' in str(exc_info.value).lower()
        assert 'end_date' in str(exc_info.value).lower()
    
    # ========================================
    # Test 3: Date Range Spans February from 31st
    # ========================================
    @pytest.mark.asyncio
    async def test_date_range_spans_february_from_31st(
        self,
        repository,
        mock_html_fetcher,
    ):
        """Test that month iteration handles February correctly when starting from 31st."""
        # Create HTML table data for each month
        # (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
        jan_data = [(31, 0.0, 6.4, 10.5, 2.3, 5.2, 3.0, 3.5)]
        feb_data = [(15, 2.5, 4.9, 8.5, 1.3, 4.2, 3.5, 4.0)]
        mar_data = [(1, 1.0, 7.9, 12.5, 3.3, 6.2, 3.0, 3.2)]
        
        table_jan = [create_html_table_from_data(2024, 1, jan_data)]
        table_feb = [create_html_table_from_data(2024, 2, feb_data)]
        table_mar = [create_html_table_from_data(2024, 3, mar_data)]
        
        # Mock will be called three times (January, February, March)
        mock_html_fetcher.get.side_effect = [table_jan, table_feb, table_mar]
        
        # This should NOT raise ValueError: day is out of range for month
        result = await repository.get_by_location_and_date_range(
            latitude=35.6895,
            longitude=139.6917,
            start_date='2024-01-31',
            end_date='2024-03-01'
        )
        
        assert result is not None
        # Should fetch January, February, and March
        assert mock_html_fetcher.get.call_count == 3
        # Should have data from all three months
        assert len(result.weather_data_list) == 3
    
    # ========================================
    # Test 4: Empty HTML Table Response
    # ========================================
    @pytest.mark.asyncio
    async def test_empty_csv_response(self, repository, mock_html_fetcher):
        """Test handling of empty HTML table response."""
        # Empty table list
        mock_html_fetcher.get.return_value = []
        
        with pytest.raises(WeatherAPIError):  # "No data table found"
            await repository.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024-01-01',
                end_date='2024-01-31'
            )
    
    # ========================================
    # Test 5: Network Timeout
    # ========================================
    @pytest.mark.asyncio
    async def test_network_timeout(self, repository, mock_html_fetcher):
        """Test handling of network timeout."""
        mock_html_fetcher.get.side_effect = HtmlFetchError(
            "Connection timeout"
        )
        
        with pytest.raises(WeatherAPIError) as exc_info:
            await repository.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024-01-01',
                end_date='2024-01-31'
            )
        
        assert 'download' in str(exc_info.value).lower() or 'timeout' in str(exc_info.value).lower()
    
    # ========================================
    # Test 6: CSV Encoding Error
    # ========================================
    @pytest.mark.asyncio
    async def test_csv_encoding_error(self, repository, mock_html_fetcher):
        """Test handling of CSV encoding error."""
        mock_html_fetcher.get.side_effect = HtmlFetchError(
            "Failed to decode CSV with encoding shift_jis"
        )
        
        with pytest.raises(WeatherAPIError):
            await repository.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024-01-01',
                end_date='2024-01-31'
            )
    
    # ========================================
    # Test 7: All Null Temperature Values
    # ========================================
    @pytest.mark.xfail(reason="Data quality validation not implemented yet")
    @pytest.mark.asyncio
    async def test_all_null_temperature_values(self, repository, mock_html_fetcher):
        """Test handling of HTML table with all null temperature values."""
        # (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
        data_rows = [
            (1, 0.0, None, None, None, 5.2, 3.0, 3.5),
            (2, 2.5, None, None, None, 3.1, 3.8, 4.2),
        ]
        table = [create_html_table_from_data(2024, 1, data_rows)]
        mock_html_fetcher.get.return_value = table
        
        result = await repository.get_by_location_and_date_range(
            latitude=35.6895,
            longitude=139.6917,
            start_date='2024-01-01',
            end_date='2024-01-02'
        )
        
        # Should still return data but with None temperatures
        assert len(result.weather_data_list) == 2
        assert result.weather_data_list[0].temperature_2m_max is None
    
    # ========================================
    # Test 8: Negative Precipitation
    # ========================================
    @pytest.mark.asyncio
    async def test_negative_precipitation(self, repository, mock_html_fetcher):
        """Test that negative precipitation is handled properly."""
        # (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
        data_rows = [(1, -5.0, 6.4, 10.5, 2.3, 5.2, 3.0, 3.5)]  # Invalid: negative precip
        table = [create_html_table_from_data(2024, 1, data_rows)]
        mock_html_fetcher.get.return_value = table
        
        # Should skip invalid data and raise WeatherDataNotFoundError
        with pytest.raises(WeatherDataNotFoundError):
            await repository.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024-01-01',
                end_date='2024-01-01'
            )
    
    # ========================================
    # Test 9: Temperature Inversion
    # ========================================
    @pytest.mark.asyncio
    async def test_temperature_inversion(self, repository, mock_html_fetcher):
        """Test handling of max temp < min temp (data quality issue)."""
        # (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
        data_rows = [(1, 0.0, 7.5, 5.0, 10.0, 5.2, 3.0, 3.5)]  # Invalid: max < min
        table = [create_html_table_from_data(2024, 1, data_rows)]
        mock_html_fetcher.get.return_value = table
        
        # Should skip invalid data and raise WeatherDataNotFoundError
        with pytest.raises(WeatherDataNotFoundError):
            await repository.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024-01-01',
                end_date='2024-01-01'
            )
    
    # ========================================
    # Test 10: Distance Calculation Accuracy
    # ========================================
    @pytest.mark.xfail(reason="Euclidean distance used instead of Haversine")
    def test_distance_calculation_hokkaido_okinawa(self, repository):
        """Test that distance calculation is geographically accurate."""
        # Hokkaido (Sapporo)
        sapporo_lat, sapporo_lon = 43.0642, 141.3469
        # Okinawa (Naha)
        naha_lat, naha_lon = 26.2124, 127.6809
        
        # Location between them (Tokyo-ish)
        test_lat, test_lon = 35.6895, 139.6917
        
        # Find nearest from Sapporo's perspective
        prec_no1, block_no1, name1 = repository._find_nearest_location(
            sapporo_lat, sapporo_lon
        )
        assert name1 == "札幌"
        
        # Find nearest from Naha's perspective
        prec_no2, block_no2, name2 = repository._find_nearest_location(
            naha_lat, naha_lon
        )
        assert name2 == "那覇"
        
        # Tokyo should find Tokyo, not confused by bad distance calculation
        prec_no3, block_no3, name3 = repository._find_nearest_location(
            test_lat, test_lon
        )
        assert name3 == "東京"
    
    # ========================================
    # Test 11: Session Cleanup on Error
    # ========================================
    @pytest.mark.xfail(reason="Resource leak - session not cleaned up on error")
    @pytest.mark.asyncio
    async def test_session_cleanup_on_error(self):
        """Test that CSV downloader cleans up resources on error."""
        from agrr_core.framework.repositories.csv_downloader import CsvDownloader
        
        downloader = CsvDownloader(timeout=1)
        
        try:
            await downloader.get("http://invalid-url-that-will-fail.test")
        except HtmlFetchError:
            pass  # Expected
        
        # Session should be closed or in a clean state
        # This test documents the expected cleanup behavior
        if hasattr(downloader, 'session'):
            # For requests.Session, check it's closed
            assert downloader.session is None or hasattr(downloader.session, '_closed')
    
    # ========================================
    # Test 12: Partial Month Failure
    # ========================================
    @pytest.mark.xfail(reason="Error handling for partial failures not clear")
    @pytest.mark.asyncio
    async def test_partial_month_failure(self, repository, mock_html_fetcher, valid_csv_data):
        """Test behavior when some months succeed and others fail."""
        # First month succeeds, second month fails, third succeeds
        mock_html_fetcher.get.side_effect = [
            valid_csv_data,  # January - success
            HtmlFetchError("Server error"),  # February - fail
            valid_csv_data,  # March - success
        ]
        
        # Should this succeed with partial data or fail completely?
        # This test documents expected behavior
        try:
            result = await repository.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024-01-01',
                end_date='2024-03-31'
            )
            # If it succeeds, should have data from Jan and Mar only
            assert len(result.weather_data_list) > 0
        except WeatherAPIError:
            # Or it could fail completely - document which is expected
            pass
    
    # ========================================
    # Test 13: Duplicate Dates in CSV
    # ========================================
    @pytest.mark.xfail(reason="Duplicate date handling not implemented")
    @pytest.mark.asyncio
    async def test_duplicate_dates_in_csv(self, repository, mock_html_fetcher):
        """Test handling of duplicate dates in HTML table."""
        # (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
        data_rows = [
            (1, 0.0, 6.4, 10.5, 2.3, 5.2, 3.0, 3.5),  # Duplicate day 1
            (1, 1.0, 6.8, 11.0, 2.5, 4.8, 3.3, 3.8),  # Duplicate day 1
            (2, 2.5, 7.2, 11.2, 3.1, 3.1, 3.8, 4.2),
        ]
        table = [create_html_table_from_data(2024, 1, data_rows)]
        mock_html_fetcher.get.return_value = table
        
        result = await repository.get_by_location_and_date_range(
            latitude=35.6895,
            longitude=139.6917,
            start_date='2024-01-01',
            end_date='2024-01-02'
        )
        
        # Should either take first, last, or average
        # Or raise error for data quality
        # This test documents expected behavior
        assert len(result.weather_data_list) == 2  # Deduplicated
    
    # ========================================
    # Test 14: Missing Required Columns
    # ========================================
    @pytest.mark.xfail(reason="Column validation not implemented")
    @pytest.mark.asyncio
    async def test_missing_required_columns(self, repository, mock_html_fetcher):
        """Test handling of HTML table with missing cells (short rows)."""
        # Create a table with incomplete rows (missing cells)
        # This simulates missing data columns
        incomplete_row = TableRow(cells=[
            '1',  # day
            '1013.0',  # pressure local
            '1023.0',  # pressure sea
            '0.0',  # precip
            # Missing all other cells!
        ])
        table = HtmlTable(
            headers=[],
            rows=[incomplete_row],
            table_id='tablefix1'
        )
        mock_html_fetcher.get.return_value = [table]
        
        result = await repository.get_by_location_and_date_range(
            latitude=35.6895,
            longitude=139.6917,
            start_date='2024-01-01',
            end_date='2024-01-01'
        )
        
        # Should handle missing columns gracefully
        # Either skip the row or fill with None
        assert result.weather_data_list is not None
        if len(result.weather_data_list) > 0:
            assert result.weather_data_list[0].temperature_2m_max is None


class TestWeatherJMARepositoryEdgeCases:
    """Additional edge case tests."""
    
    @pytest.fixture
    def mock_html_fetcher(self):
        service = AsyncMock(spec=HtmlTableFetchInterface)
        return service
    
    @pytest.fixture
    def repository(self, mock_html_fetcher):
        return WeatherJMARepository(mock_html_fetcher)
    
    @pytest.mark.asyncio
    async def test_leap_year_february_29(self, repository, mock_html_fetcher):
        """Test handling of leap year (Feb 29)."""
        # (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
        data_rows = [(29, 0.0, 6.4, 10.5, 2.3, 5.2, 3.0, 3.5)]
        table = [create_html_table_from_data(2024, 2, data_rows)]
        mock_html_fetcher.get.return_value = table
        
        result = await repository.get_by_location_and_date_range(
            latitude=35.6895,
            longitude=139.6917,
            start_date='2024-02-29',
            end_date='2024-02-29'
        )
        
        assert len(result.weather_data_list) == 1
        assert result.weather_data_list[0].time.day == 29
    
    @pytest.mark.xfail(reason="Year boundary crossing issue - January data not returned")
    @pytest.mark.asyncio
    async def test_year_boundary_crossing(self, repository, mock_html_fetcher):
        """Test date range crossing year boundary."""
        # Setup: Two separate HTML table responses for Dec and Jan
        # (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
        dec_data = [(31, 0.0, 2.5, 5.0, 0.0, 3.0, 1.5, 2.0)]
        jan_data = [(1, 0.0, 3.5, 6.0, 1.0, 4.0, 2.0, 2.5)]
        
        table_dec = [create_html_table_from_data(2023, 12, dec_data)]
        table_jan = [create_html_table_from_data(2024, 1, jan_data)]
        
        # Mock will be called twice (December, then January)
        mock_html_fetcher.get.side_effect = [table_dec, table_jan]
        
        result = await repository.get_by_location_and_date_range(
            latitude=35.6895,
            longitude=139.6917,
            start_date='2023-12-31',
            end_date='2024-01-01'
        )
        
        assert len(result.weather_data_list) == 2
        # Should fetch both December 2023 and January 2024
        assert mock_html_fetcher.get.call_count == 2

