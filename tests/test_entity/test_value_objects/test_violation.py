"""Tests for Violation value object."""

import pytest

from agrr_core.entity.value_objects.violation import Violation
from agrr_core.entity.value_objects.violation_type import ViolationType

class TestViolation:
    """Test Violation value object."""
    
    def test_create_valid_violation(self):
        """Test creating a valid violation."""
        violation = Violation(
            violation_type=ViolationType.FALLOW_PERIOD,
            code="FALLOW_001",
            message="Test violation",
            severity="error",
            impact_ratio=1.0
        )
        
        assert violation.violation_type == ViolationType.FALLOW_PERIOD
        assert violation.code == "FALLOW_001"
        assert violation.message == "Test violation"
        assert violation.severity == "error"
        assert violation.impact_ratio == 1.0
        assert violation.details is None
    
    def test_violation_with_details(self):
        """Test violation with additional details."""
        violation = Violation(
            violation_type=ViolationType.CONTINUOUS_CULTIVATION,
            code="CONT_CULT_001",
            message="Test violation",
            severity="warning",
            impact_ratio=0.7,
            details="Additional context"
        )
        
        assert violation.details == "Additional context"
        assert violation.impact_ratio == 0.7
    
    def test_violation_validation_empty_code(self):
        """Test that empty code raises ValueError."""
        with pytest.raises(ValueError, match="code cannot be empty"):
            Violation(
                violation_type=ViolationType.FALLOW_PERIOD,
                code="",
                message="Test",
                severity="error"
            )
    
    def test_violation_validation_empty_message(self):
        """Test that empty message raises ValueError."""
        with pytest.raises(ValueError, match="message cannot be empty"):
            Violation(
                violation_type=ViolationType.FALLOW_PERIOD,
                code="TEST_001",
                message="",
                severity="error"
            )
    
    def test_violation_validation_invalid_severity(self):
        """Test that invalid severity raises ValueError."""
        with pytest.raises(ValueError, match="Invalid severity"):
            Violation(
                violation_type=ViolationType.FALLOW_PERIOD,
                code="TEST_001",
                message="Test",
                severity="invalid"
            )
    
    def test_violation_validation_negative_impact_ratio(self):
        """Test that negative impact ratio raises ValueError."""
        with pytest.raises(ValueError, match="Impact ratio must be between 0.0 and 1.0"):
            Violation(
                violation_type=ViolationType.FALLOW_PERIOD,
                code="TEST_001",
                message="Test",
                severity="error",
                impact_ratio=-0.1
            )
    
    def test_violation_validation_impact_ratio_over_one(self):
        """Test that impact ratio > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Impact ratio must be between 0.0 and 1.0"):
            Violation(
                violation_type=ViolationType.FALLOW_PERIOD,
                code="TEST_001",
                message="Test",
                severity="error",
                impact_ratio=1.5
            )
    
    def test_is_error_true(self):
        """Test is_error() returns True for error severity."""
        violation = Violation(
            violation_type=ViolationType.FALLOW_PERIOD,
            code="TEST_001",
            message="Test",
            severity="error"
        )
        
        assert violation.is_error() is True
        assert violation.is_warning() is False
    
    def test_is_warning_true(self):
        """Test is_warning() returns True for warning severity."""
        violation = Violation(
            violation_type=ViolationType.CONTINUOUS_CULTIVATION,
            code="TEST_001",
            message="Test",
            severity="warning"
        )
        
        assert violation.is_warning() is True
        assert violation.is_error() is False
    
    def test_violation_is_immutable(self):
        """Test that violation is immutable (frozen dataclass)."""
        violation = Violation(
            violation_type=ViolationType.FALLOW_PERIOD,
            code="TEST_001",
            message="Test",
            severity="error"
        )
        
        with pytest.raises(Exception):  # TypeError: cannot assign to field
            violation.code = "NEW_CODE"
