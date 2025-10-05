"""Tests for CLI weather presenter."""

import pytest
import json
from io import StringIO
from datetime import datetime

from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO


class TestCLIWeatherPresenter:
    """Test cases for CLI weather presenter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.output_stream = StringIO()
        self.presenter = WeatherCLIPresenter(output_stream=self.output_stream)
    
    def test_format_weather_data_dto(self):
        """Test formatting weather data DTO."""
        dto = WeatherDataResponseDTO(
            time="2024-01-15T00:00:00Z",
            temperature_2m_max=15.5,
            temperature_2m_min=8.2,
            temperature_2m_mean=11.8,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
            sunshine_hours=8.0
        )
        
        result = self.presenter.format_weather_data_dto(dto)
        
        assert result["time"] == "2024-01-15T00:00:00Z"
        assert result["temperature_2m_max"] == 15.5
        assert result["temperature_2m_min"] == 8.2
        assert result["temperature_2m_mean"] == 11.8
        assert result["precipitation_sum"] == 5.0
        assert result["sunshine_duration"] == 28800.0
        assert result["sunshine_hours"] == 8.0
    
    def test_format_weather_data_list_dto(self):
        """Test formatting weather data list DTO."""
        dto1 = WeatherDataResponseDTO(
            time="2024-01-15T00:00:00Z",
            temperature_2m_max=15.5,
            temperature_2m_min=8.2,
            temperature_2m_mean=11.8,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
            sunshine_hours=8.0
        )
        
        dto2 = WeatherDataResponseDTO(
            time="2024-01-16T00:00:00Z",
            temperature_2m_max=18.3,
            temperature_2m_min=10.1,
            temperature_2m_mean=14.2,
            precipitation_sum=0.0,
            sunshine_duration=32400.0,
            sunshine_hours=9.0
        )
        
        list_dto = WeatherDataListResponseDTO(
            data=[dto1, dto2],
            total_count=2
        )
        
        result = self.presenter.format_weather_data_list_dto(list_dto)
        
        assert len(result["data"]) == 2
        assert result["total_count"] == 2
        assert result["data"][0]["time"] == "2024-01-15T00:00:00Z"
        assert result["data"][1]["time"] == "2024-01-16T00:00:00Z"
    
    def test_format_error(self):
        """Test formatting error response."""
        result = self.presenter.format_error("Test error message", "TEST_ERROR")
        
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test error message"
        assert result["success"] is False
    
    def test_format_success(self):
        """Test formatting success response."""
        data = {"test": "data"}
        result = self.presenter.format_success(data)
        
        assert result["success"] is True
        assert result["data"] == data
    
    def test_display_weather_data_empty(self):
        """Test displaying empty weather data."""
        list_dto = WeatherDataListResponseDTO(data=[], total_count=0)
        
        self.presenter.display_weather_data(list_dto)
        output = self.output_stream.getvalue()
        
        assert "No weather data available" in output
    
    def test_display_weather_data_with_data(self):
        """Test displaying weather data with actual data."""
        dto = WeatherDataResponseDTO(
            time="2024-01-15T00:00:00Z",
            temperature_2m_max=15.5,
            temperature_2m_min=8.2,
            temperature_2m_mean=11.8,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
            sunshine_hours=8.0
        )
        
        list_dto = WeatherDataListResponseDTO(data=[dto], total_count=1)
        
        self.presenter.display_weather_data(list_dto)
        output = self.output_stream.getvalue()
        
        assert "WEATHER FORECAST" in output
        assert "2024-01-15" in output
        assert "15.5°C" in output
        assert "8.2°C" in output
        assert "11.8°C" in output
        assert "5.0mm" in output
        assert "8.0h" in output
        assert "Total records: 1" in output
    
    def test_display_error(self):
        """Test displaying error message."""
        self.presenter.display_error("Test error", "TEST_ERROR")
        output = self.output_stream.getvalue()
        
        assert "❌ Error [TEST_ERROR]: Test error" in output
    
    def test_display_success_message(self):
        """Test displaying success message."""
        self.presenter.display_success_message("Test success")
        output = self.output_stream.getvalue()
        
        assert "✅ Test success" in output
    
    def test_format_date(self):
        """Test date formatting."""
        # Test ISO format
        result = self.presenter._format_date("2024-01-15T00:00:00Z")
        assert result == "2024-01-15"
        
        # Test invalid format fallback
        result = self.presenter._format_date("invalid-date")
        assert result == "invalid-date"
    
    def test_format_temperature(self):
        """Test temperature formatting."""
        assert self.presenter._format_temperature(15.5) == "15.5°C"
        assert self.presenter._format_temperature(None) == "N/A"
    
    def test_format_precipitation(self):
        """Test precipitation formatting."""
        assert self.presenter._format_precipitation(5.0) == "5.0mm"
        assert self.presenter._format_precipitation(None) == "N/A"
    
    def test_format_sunshine(self):
        """Test sunshine formatting."""
        assert self.presenter._format_sunshine(8.5) == "8.5h"
        assert self.presenter._format_sunshine(None) == "N/A"
    
    def test_display_weather_data_json(self):
        """Test displaying weather data in JSON format."""
        dto = WeatherDataResponseDTO(
            time="2024-01-15T00:00:00Z",
            temperature_2m_max=15.5,
            temperature_2m_min=8.2,
            temperature_2m_mean=11.8,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
            sunshine_hours=8.0
        )
        
        list_dto = WeatherDataListResponseDTO(data=[dto], total_count=1)
        
        self.presenter.display_weather_data_json(list_dto)
        output = self.output_stream.getvalue()
        
        # Parse JSON output
        result = json.loads(output)
        
        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]["data"]) == 1
        assert result["data"]["total_count"] == 1
        assert result["data"]["data"][0]["time"] == "2024-01-15T00:00:00Z"
        assert result["data"]["data"][0]["temperature_2m_max"] == 15.5
        assert result["data"]["data"][0]["temperature_2m_min"] == 8.2
        assert result["data"]["data"][0]["temperature_2m_mean"] == 11.8
    
    def test_display_weather_data_json_empty(self):
        """Test displaying empty weather data in JSON format."""
        list_dto = WeatherDataListResponseDTO(data=[], total_count=0)
        
        self.presenter.display_weather_data_json(list_dto)
        output = self.output_stream.getvalue()
        
        # Parse JSON output
        result = json.loads(output)
        
        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]["data"]) == 0
        assert result["data"]["total_count"] == 0
    
    def test_display_error_json(self):
        """Test displaying error message in JSON format."""
        self.presenter.display_error("Test error", "TEST_ERROR", json_output=True)
        output = self.output_stream.getvalue()
        
        # Parse JSON output
        result = json.loads(output)
        
        assert result["success"] is False
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test error"
    
    def test_display_error_text(self):
        """Test displaying error message in text format."""
        self.presenter.display_error("Test error", "TEST_ERROR", json_output=False)
        output = self.output_stream.getvalue()
        
        # Should not be valid JSON
        assert "❌ Error [TEST_ERROR]: Test error" in output
    
    def test_display_weather_data_with_location(self):
        """Test displaying weather data with location information."""
        dto = WeatherDataResponseDTO(
            time="2024-01-15T00:00:00Z",
            temperature_2m_max=15.5,
            temperature_2m_min=8.2,
            temperature_2m_mean=11.8,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
            sunshine_hours=8.0
        )
        
        location_dto = LocationResponseDTO(
            latitude=35.6762,
            longitude=139.6911,
            elevation=37.0,
            timezone="Asia/Tokyo"
        )
        
        list_dto = WeatherDataListResponseDTO(
            data=[dto],
            total_count=1,
            location=location_dto
        )
        
        self.presenter.display_weather_data(list_dto)
        output = self.output_stream.getvalue()
        
        assert "WEATHER FORECAST" in output
        assert "Location: 35.6762°N, 139.6911°E" in output
        assert "Elevation: 37m" in output
        assert "Timezone: Asia/Tokyo" in output
        assert "2024-01-15" in output
    
    def test_display_weather_data_json_with_location(self):
        """Test displaying weather data in JSON format with location."""
        dto = WeatherDataResponseDTO(
            time="2024-01-15T00:00:00Z",
            temperature_2m_max=15.5,
            temperature_2m_min=8.2,
            temperature_2m_mean=11.8,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
            sunshine_hours=8.0
        )
        
        location_dto = LocationResponseDTO(
            latitude=35.6762,
            longitude=139.6911,
            elevation=37.0,
            timezone="Asia/Tokyo"
        )
        
        list_dto = WeatherDataListResponseDTO(
            data=[dto],
            total_count=1,
            location=location_dto
        )
        
        self.presenter.display_weather_data_json(list_dto)
        output = self.output_stream.getvalue()
        
        # Parse JSON output
        result = json.loads(output)
        
        assert result["success"] is True
        assert "location" in result["data"]
        assert result["data"]["location"]["latitude"] == 35.6762
        assert result["data"]["location"]["longitude"] == 139.6911
        assert result["data"]["location"]["elevation"] == 37.0
        assert result["data"]["location"]["timezone"] == "Asia/Tokyo"
