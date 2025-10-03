"""Tests for DateRange entity."""

import pytest

from agrr_core.entity import DateRange
from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError


class TestDateRange:
    """Test DateRange entity."""
    
    def test_valid_date_range(self):
        """Test creating valid DateRange."""
        date_range = DateRange(start_date="2023-01-01", end_date="2023-12-31")
        
        assert date_range.start_date == "2023-01-01"
        assert date_range.end_date == "2023-12-31"
    
    def test_invalid_date_format(self):
        """Test invalid date format."""
        with pytest.raises(InvalidDateRangeError):
            DateRange(start_date="2023/01/01", end_date="2023-12-31")
    
    def test_invalid_date_format_end(self):
        """Test invalid end date format."""
        with pytest.raises(InvalidDateRangeError):
            DateRange(start_date="2023-01-01", end_date="2023/12/31")
    
    def test_invalid_date_string(self):
        """Test invalid date string."""
        with pytest.raises(InvalidDateRangeError):
            DateRange(start_date="invalid-date", end_date="2023-12-31")
