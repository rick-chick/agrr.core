"""Tests for ForecastResponseDTO."""

import pytest

from agrr_core.usecase.dto.forecast_response_dto import ForecastResponseDTO


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
