"""Tests for PredictionResponseDTO."""

import pytest

from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.forecast_response_dto import ForecastResponseDTO
from agrr_core.usecase.dto.prediction_response_dto import PredictionResponseDTO


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
