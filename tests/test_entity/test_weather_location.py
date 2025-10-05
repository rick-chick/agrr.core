"""Tests for Location entity."""

import pytest

from agrr_core.entity import Location
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError


class TestLocation:
    """Test Location entity."""
    
    def test_valid_location(self):
        """Test creating valid Location."""
        location = Location(latitude=35.7, longitude=139.7)
        
        assert location.latitude == 35.7
        assert location.longitude == 139.7
    
    def test_invalid_latitude_too_high(self):
        """Test invalid latitude (too high)."""
        with pytest.raises(InvalidLocationError):
            Location(latitude=91.0, longitude=139.7)
    
    def test_invalid_latitude_too_low(self):
        """Test invalid latitude (too low)."""
        with pytest.raises(InvalidLocationError):
            Location(latitude=-91.0, longitude=139.7)
    
    def test_invalid_longitude_too_high(self):
        """Test invalid longitude (too high)."""
        with pytest.raises(InvalidLocationError):
            Location(latitude=35.7, longitude=181.0)
    
    def test_invalid_longitude_too_low(self):
        """Test invalid longitude (too low)."""
        with pytest.raises(InvalidLocationError):
            Location(latitude=35.7, longitude=-181.0)
    
    def test_boundary_values(self):
        """Test boundary values."""
        # Valid boundary values
        Location(latitude=90.0, longitude=180.0)
        Location(latitude=-90.0, longitude=-180.0)
