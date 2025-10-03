"""Tests for DTOs."""

import pytest

from agrr_core.usecase.dto.weather_dto import (
    WeatherDataRequestDTO,
    WeatherDataResponseDTO,
    WeatherDataListResponseDTO,
    PredictionRequestDTO,
    ForecastResponseDTO,
    PredictionResponseDTO,
)


class TestWeatherDataRequestDTO:
    """Test WeatherDataRequestDTO."""
    
    def test_creation(self):
        """Test creating WeatherDataRequestDTO."""
        dto = WeatherDataRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        assert dto.latitude == 35.7
        assert dto.longitude == 139.7
        assert dto.start_date == "2023-01-01"
        assert dto.end_date == "2023-12-31"


class TestWeatherDataResponseDTO:
    """Test WeatherDataResponseDTO."""
    
    def test_creation(self):
        """Test creating WeatherDataResponseDTO."""
        dto = WeatherDataResponseDTO(
            time="2023-01-01T00:00:00",
            temperature_2m_max=25.0,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
            sunshine_hours=8.0
        )
        
        assert dto.time == "2023-01-01T00:00:00"
        assert dto.temperature_2m_max == 25.0
        assert dto.temperature_2m_min == 15.0
        assert dto.temperature_2m_mean == 20.0
        assert dto.precipitation_sum == 5.0
        assert dto.sunshine_duration == 28800.0
        assert dto.sunshine_hours == 8.0


class TestWeatherDataListResponseDTO:
    """Test WeatherDataListResponseDTO."""
    
    def test_creation(self):
        """Test creating WeatherDataListResponseDTO."""
        data = [
            WeatherDataResponseDTO(
                time="2023-01-01T00:00:00",
                temperature_2m_mean=20.0
            ),
            WeatherDataResponseDTO(
                time="2023-01-02T00:00:00",
                temperature_2m_mean=21.0
            ),
        ]
        
        dto = WeatherDataListResponseDTO(data=data, total_count=2)
        
        assert len(dto.data) == 2
        assert dto.total_count == 2
        assert dto.data[0].time == "2023-01-01T00:00:00"
        assert dto.data[1].time == "2023-01-02T00:00:00"


class TestPredictionRequestDTO:
    """Test PredictionRequestDTO."""
    
    def test_creation_default_prediction_days(self):
        """Test creating PredictionRequestDTO with default prediction_days."""
        dto = PredictionRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        assert dto.latitude == 35.7
        assert dto.longitude == 139.7
        assert dto.start_date == "2023-01-01"
        assert dto.end_date == "2023-12-31"
        assert dto.prediction_days == 365  # Default value
    
    def test_creation_custom_prediction_days(self):
        """Test creating PredictionRequestDTO with custom prediction_days."""
        dto = PredictionRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-12-31",
            prediction_days=30
        )
        
        assert dto.prediction_days == 30


class TestForecastResponseDTO:
    """Test ForecastResponseDTO."""
    
    def test_creation(self):
        """Test creating ForecastResponseDTO."""
        dto = ForecastResponseDTO(
            date="2024-01-01T00:00:00",
            predicted_value=20.5,
            confidence_lower=18.0,
            confidence_upper=23.0
        )
        
        assert dto.date == "2024-01-01T00:00:00"
        assert dto.predicted_value == 20.5
        assert dto.confidence_lower == 18.0
        assert dto.confidence_upper == 23.0


class TestPredictionResponseDTO:
    """Test PredictionResponseDTO."""
    
    def test_creation(self):
        """Test creating PredictionResponseDTO."""
        historical_data = [
            WeatherDataResponseDTO(
                time="2023-01-01T00:00:00",
                temperature_2m_mean=20.0
            )
        ]
        
        forecast = [
            ForecastResponseDTO(
                date="2024-01-01T00:00:00",
                predicted_value=20.5,
                confidence_lower=18.0,
                confidence_upper=23.0
            )
        ]
        
        model_metrics = {
            "training_data_points": 1,
            "prediction_days": 365,
            "model_type": "Prophet"
        }
        
        dto = PredictionResponseDTO(
            historical_data=historical_data,
            forecast=forecast,
            model_metrics=model_metrics
        )
        
        assert len(dto.historical_data) == 1
        assert len(dto.forecast) == 1
        assert dto.model_metrics == model_metrics
        assert dto.historical_data[0].temperature_2m_mean == 20.0
        assert dto.forecast[0].predicted_value == 20.5
    
    def test_creation_without_model_metrics(self):
        """Test creating PredictionResponseDTO without model_metrics."""
        historical_data = [
            WeatherDataResponseDTO(
                time="2023-01-01T00:00:00",
                temperature_2m_mean=20.0
            )
        ]
        
        forecast = [
            ForecastResponseDTO(
                date="2024-01-01T00:00:00",
                predicted_value=20.5
            )
        ]
        
        dto = PredictionResponseDTO(
            historical_data=historical_data,
            forecast=forecast
        )
        
        assert len(dto.historical_data) == 1
        assert len(dto.forecast) == 1
        assert dto.model_metrics is None
