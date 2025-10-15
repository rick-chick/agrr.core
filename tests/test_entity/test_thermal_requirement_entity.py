"""Tests for ThermalRequirement entity."""

import pytest

from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement


class TestThermalRequirement:
    """Test ThermalRequirement entity."""

    def test_basic_thermal_requirement(self):
        """Test basic thermal requirement creation."""
        thermal = ThermalRequirement(required_gdd=1000.0)
        
        assert thermal.required_gdd == 1000.0
        assert thermal.harvest_start_gdd is None

    def test_thermal_requirement_with_harvest_start(self):
        """Test thermal requirement with harvest_start_gdd."""
        thermal = ThermalRequirement(
            required_gdd=2000.0,
            harvest_start_gdd=200.0
        )
        
        assert thermal.required_gdd == 2000.0
        assert thermal.harvest_start_gdd == 200.0

    def test_is_met_basic(self):
        """Test is_met method."""
        thermal = ThermalRequirement(required_gdd=1000.0)
        
        assert not thermal.is_met(500.0)
        assert not thermal.is_met(999.9)
        assert thermal.is_met(1000.0)
        assert thermal.is_met(1500.0)

    def test_is_harvest_started_without_harvest_start_gdd(self):
        """Test is_harvest_started when harvest_start_gdd is None."""
        thermal = ThermalRequirement(required_gdd=1000.0)
        
        # When harvest_start_gdd is None, is_harvest_started should behave like is_met
        assert not thermal.is_harvest_started(500.0)
        assert not thermal.is_harvest_started(999.9)
        assert thermal.is_harvest_started(1000.0)
        assert thermal.is_harvest_started(1500.0)

    def test_is_harvest_started_with_harvest_start_gdd(self):
        """Test is_harvest_started with harvest_start_gdd."""
        thermal = ThermalRequirement(
            required_gdd=2000.0,
            harvest_start_gdd=200.0
        )
        
        # Before harvest start
        assert not thermal.is_harvest_started(100.0)
        assert not thermal.is_harvest_started(199.9)
        
        # Harvest started but not complete
        assert thermal.is_harvest_started(200.0)
        assert thermal.is_harvest_started(1000.0)
        assert thermal.is_harvest_started(1999.9)
        
        # Harvest complete
        assert thermal.is_harvest_started(2000.0)
        assert thermal.is_harvest_started(2500.0)
        
        # Stage is not complete at harvest start
        assert not thermal.is_met(200.0)
        assert not thermal.is_met(1000.0)
        
        # Stage is complete at required_gdd
        assert thermal.is_met(2000.0)
        assert thermal.is_met(2500.0)

    def test_harvest_duration_calculation(self):
        """Test harvest duration calculation."""
        thermal = ThermalRequirement(
            required_gdd=2200.0,
            harvest_start_gdd=200.0
        )
        
        # Harvest duration = required_gdd - harvest_start_gdd
        harvest_duration = thermal.required_gdd - thermal.harvest_start_gdd
        assert harvest_duration == 2000.0

    def test_negative_required_gdd_raises_error(self):
        """Test that negative required_gdd raises ValueError."""
        with pytest.raises(ValueError, match="required_gdd must be positive"):
            ThermalRequirement(required_gdd=-100.0)

    def test_zero_required_gdd_raises_error(self):
        """Test that zero required_gdd raises ValueError."""
        with pytest.raises(ValueError, match="required_gdd must be positive"):
            ThermalRequirement(required_gdd=0.0)

    def test_negative_harvest_start_gdd_raises_error(self):
        """Test that negative harvest_start_gdd raises ValueError."""
        with pytest.raises(ValueError, match="harvest_start_gdd must be positive"):
            ThermalRequirement(
                required_gdd=2000.0,
                harvest_start_gdd=-100.0
            )

    def test_zero_harvest_start_gdd_raises_error(self):
        """Test that zero harvest_start_gdd raises ValueError."""
        with pytest.raises(ValueError, match="harvest_start_gdd must be positive"):
            ThermalRequirement(
                required_gdd=2000.0,
                harvest_start_gdd=0.0
            )

    def test_harvest_start_gdd_greater_than_required_gdd_raises_error(self):
        """Test that harvest_start_gdd >= required_gdd raises ValueError."""
        with pytest.raises(ValueError, match="harvest_start_gdd .* must be less than"):
            ThermalRequirement(
                required_gdd=2000.0,
                harvest_start_gdd=2000.0
            )
        
        with pytest.raises(ValueError, match="harvest_start_gdd .* must be less than"):
            ThermalRequirement(
                required_gdd=2000.0,
                harvest_start_gdd=2500.0
            )

    def test_fruiting_crop_eggplant_example(self):
        """Test realistic example: Eggplant harvest stage."""
        # Eggplant harvest stage: 
        # - First harvest at 200 GDD
        # - Harvest ends at 2200 GDD
        # - Harvest duration: 2000 GDD (60-90 days)
        thermal = ThermalRequirement(
            required_gdd=2200.0,
            harvest_start_gdd=200.0
        )
        
        # Before any harvest
        assert not thermal.is_harvest_started(150.0)
        assert not thermal.is_met(150.0)
        
        # First harvest possible
        assert thermal.is_harvest_started(200.0)
        assert not thermal.is_met(200.0)  # But stage not complete
        
        # Mid-harvest period
        assert thermal.is_harvest_started(1000.0)
        assert not thermal.is_met(1000.0)  # Still harvesting
        
        # Harvest ends
        assert thermal.is_harvest_started(2200.0)
        assert thermal.is_met(2200.0)  # Stage complete

    def test_single_harvest_crop_rice_example(self):
        """Test realistic example: Rice (single harvest, no harvest_start_gdd)."""
        # Rice maturity stage: single harvest at 800 GDD
        thermal = ThermalRequirement(required_gdd=800.0)
        
        # Before maturity
        assert not thermal.is_harvest_started(700.0)
        assert not thermal.is_met(700.0)
        
        # At maturity (harvest and stage completion are the same)
        assert thermal.is_harvest_started(800.0)
        assert thermal.is_met(800.0)
        
        # After maturity
        assert thermal.is_harvest_started(900.0)
        assert thermal.is_met(900.0)

    def test_backward_compatibility(self):
        """Test that existing code without harvest_start_gdd works unchanged."""
        # Old code pattern: just required_gdd
        thermal = ThermalRequirement(required_gdd=1000.0)
        
        # Should work exactly as before
        assert thermal.required_gdd == 1000.0
        assert thermal.is_met(1000.0)
        assert not thermal.is_met(500.0)
        
        # is_harvest_started should behave like is_met when harvest_start_gdd is None
        assert thermal.is_harvest_started(1000.0)
        assert not thermal.is_harvest_started(500.0)

