"""Tests for LinearInterpolationService."""

import pytest
import numpy as np

from agrr_core.adapter.services.interpolation_utils import LinearInterpolationService


class TestLinearInterpolationService:
    """Test cases for LinearInterpolationService."""
    
    def test_interpolate_missing_middle_value(self):
        """Test interpolation for missing value in the middle."""
        # Arrange
        data = [10.0, np.nan, 20.0]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert: Should be linear interpolation (10 + 20) / 2 = 15
        assert result == [10.0, 15.0, 20.0]
    
    def test_interpolate_missing_beginning_value(self):
        """Test forward fill for missing value at beginning."""
        # Arrange
        data = [np.nan, 15.0, 20.0]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert: Should use first valid value (forward fill)
        assert result == [15.0, 15.0, 20.0]
    
    def test_interpolate_missing_end_value(self):
        """Test backward fill for missing value at end."""
        # Arrange
        data = [10.0, 15.0, np.nan]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert: Should use last valid value (backward fill)
        assert result == [10.0, 15.0, 15.0]
    
    def test_interpolate_multiple_missing_values(self):
        """Test interpolation for multiple consecutive missing values."""
        # Arrange
        data = [10.0, np.nan, np.nan, np.nan, 30.0]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert: Should be linear interpolation
        # Day 1: 10.0
        # Day 2: 10.0 + (30.0 - 10.0) * 1/4 = 15.0
        # Day 3: 10.0 + (30.0 - 10.0) * 2/4 = 20.0
        # Day 4: 10.0 + (30.0 - 10.0) * 3/4 = 25.0
        # Day 5: 30.0
        assert result == [10.0, 15.0, 20.0, 25.0, 30.0]
    
    def test_interpolate_multiple_beginning_values(self):
        """Test forward fill for multiple missing values at beginning."""
        # Arrange
        data = [np.nan, np.nan, 20.0, 25.0]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert: Should use first valid value for all
        assert result == [20.0, 20.0, 20.0, 25.0]
    
    def test_interpolate_multiple_end_values(self):
        """Test backward fill for multiple missing values at end."""
        # Arrange
        data = [10.0, 15.0, np.nan, np.nan]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert: Should use last valid value for all
        assert result == [10.0, 15.0, 15.0, 15.0]
    
    def test_interpolate_no_missing_values(self):
        """Test that data without missing values is returned unchanged."""
        # Arrange
        data = [10.0, 15.0, 20.0]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert: Should be unchanged
        assert result == [10.0, 15.0, 20.0]
    
    def test_interpolate_all_missing_raises_error(self):
        """Test that all missing values raises error."""
        # Arrange
        data = [np.nan, np.nan, np.nan]
        
        # Act & Assert
        with pytest.raises(ValueError, match="All values are missing"):
            LinearInterpolationService.interpolate_missing_values(data)
    
    def test_interpolate_empty_list(self):
        """Test that empty list is returned unchanged."""
        # Arrange
        data = []
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert
        assert result == []
    
    def test_interpolate_single_value(self):
        """Test interpolation with single value."""
        # Arrange
        data = [15.0]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert
        assert result == [15.0]
    
    def test_interpolate_single_missing_value_raises_error(self):
        """Test that single missing value raises error."""
        # Arrange
        data = [np.nan]
        
        # Act & Assert
        with pytest.raises(ValueError, match="All values are missing"):
            LinearInterpolationService.interpolate_missing_values(data)
    
    def test_interpolate_complex_pattern(self):
        """Test interpolation with complex missing pattern."""
        # Arrange: Missing at beginning, middle, and end
        data = [np.nan, np.nan, 10.0, np.nan, 20.0, np.nan, np.nan]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert:
        # [0,1]: Forward fill with 10.0
        # [2]: 10.0 (existing)
        # [3]: Linear interpolation between 10.0 and 20.0 = 15.0
        # [4]: 20.0 (existing)
        # [5,6]: Backward fill with 20.0
        assert result == [10.0, 10.0, 10.0, 15.0, 20.0, 20.0, 20.0]
    
    def test_interpolate_preserves_float_precision(self):
        """Test that interpolation preserves float precision."""
        # Arrange
        data = [10.5, np.nan, 15.3]
        
        # Act
        result = LinearInterpolationService.interpolate_missing_values(data)
        
        # Assert: Should preserve precision
        expected = (10.5 + 15.3) / 2
        assert result[1] == pytest.approx(expected)

