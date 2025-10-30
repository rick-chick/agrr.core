"""Tests for PredictionRequestDTO."""

import pytest

from agrr_core.usecase.dto.prediction_request_dto import PredictionRequestDTO

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
