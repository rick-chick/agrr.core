"""Tests for YieldImpactAccumulator value object.

Tests the accumulation of daily stress impacts and yield factor calculation.
"""

import pytest

from agrr_core.entity.value_objects.yield_impact_accumulator import (
    YieldImpactAccumulator,
)

class TestYieldImpactAccumulatorBasics:
    """Test basic functionality of YieldImpactAccumulator."""
    
    def test_initial_state(self):
        """Test that accumulator starts with no impact."""
        accumulator = YieldImpactAccumulator()
        assert accumulator.get_yield_factor() == 1.0
        assert accumulator.get_yield_loss_percentage() == 0.0
    
    def test_no_stress_maintains_full_yield(self):
        """Test that no stress results in yield_factor = 1.0."""
        accumulator = YieldImpactAccumulator()
        no_stress = {"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        
        # Accumulate 10 days of no stress
        for _ in range(10):
            accumulator.accumulate_daily_impact(no_stress)
        
        assert accumulator.get_yield_factor() == 1.0
        assert accumulator.get_yield_loss_percentage() == 0.0

class TestStressAccumulation:
    """Test stress accumulation scenarios."""
    
    def test_single_day_high_temp_stress(self):
        """Test accumulation of single day high temperature stress."""
        accumulator = YieldImpactAccumulator()
        daily_impacts = {"high_temp": 0.05, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        
        accumulator.accumulate_daily_impact(daily_impacts)
        
        # Expected: 1.0 * (1 - 0.05) = 0.95
        assert accumulator.get_yield_factor() == pytest.approx(0.95, rel=1e-6)
        assert accumulator.get_yield_loss_percentage() == pytest.approx(5.0, rel=1e-6)
    
    def test_multiple_days_same_stress(self):
        """Test accumulation over multiple days with same stress."""
        accumulator = YieldImpactAccumulator()
        daily_impacts = {"high_temp": 0.05, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        
        # 3 days of 5% daily impact
        for _ in range(3):
            accumulator.accumulate_daily_impact(daily_impacts)
        
        # Expected: (1-0.05)^3 = 0.95^3 ≈ 0.857375
        expected_factor = 0.95 ** 3
        assert accumulator.get_yield_factor() == pytest.approx(expected_factor, rel=1e-6)
        assert accumulator.get_yield_loss_percentage() == pytest.approx((1 - expected_factor) * 100, rel=1e-6)
    
    def test_multiple_stress_types_single_day(self):
        """Test multiple stress types occurring on the same day."""
        accumulator = YieldImpactAccumulator()
        daily_impacts = {
            "high_temp": 0.05,  # 5% impact
            "low_temp": 0.0,
            "frost": 0.0,
            "sterility": 0.10,  # 10% impact
        }
        
        accumulator.accumulate_daily_impact(daily_impacts)
        
        # Expected: (1 - 0.05) * (1 - 0.10) = 0.95 * 0.90 = 0.855
        assert accumulator.get_yield_factor() == pytest.approx(0.855, rel=1e-6)
    
    def test_severe_stress_accumulation(self):
        """Test severe stress leading to significant yield loss."""
        accumulator = YieldImpactAccumulator()
        
        # 5 days of 20% daily impact (severe stress)
        severe_stress = {"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.20}
        for _ in range(5):
            accumulator.accumulate_daily_impact(severe_stress)
        
        # Expected: (1 - 0.20)^5 = 0.80^5 ≈ 0.32768
        expected_factor = 0.80 ** 5
        assert accumulator.get_yield_factor() == pytest.approx(expected_factor, rel=1e-6)
        assert accumulator.get_yield_loss_percentage() > 60  # More than 60% loss
    
    def test_frost_damage(self):
        """Test frost damage impact."""
        accumulator = YieldImpactAccumulator()
        
        # Single day of frost (15% impact)
        frost_day = {"high_temp": 0.0, "low_temp": 0.0, "frost": 0.15, "sterility": 0.0}
        accumulator.accumulate_daily_impact(frost_day)
        
        # Expected: 1.0 * (1 - 0.15) = 0.85
        assert accumulator.get_yield_factor() == pytest.approx(0.85, rel=1e-6)
        assert accumulator.get_yield_loss_percentage() == pytest.approx(15.0, rel=1e-6)
    
    def test_mixed_stress_realistic_scenario(self):
        """Test realistic scenario with varied daily stresses."""
        accumulator = YieldImpactAccumulator()
        
        # Day 1-3: No stress
        no_stress = {"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        for _ in range(3):
            accumulator.accumulate_daily_impact(no_stress)
        
        # Day 4-6: High temp stress (5% each day)
        high_temp = {"high_temp": 0.05, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        for _ in range(3):
            accumulator.accumulate_daily_impact(high_temp)
        
        # Day 7: Severe sterility risk (20%)
        sterility = {"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.20}
        accumulator.accumulate_daily_impact(sterility)
        
        # Day 8-10: No stress (recovery)
        for _ in range(3):
            accumulator.accumulate_daily_impact(no_stress)
        
        # Expected: 1.0 * (0.95^3) * 0.80 = 0.857375 * 0.80 ≈ 0.6859
        expected_factor = (0.95 ** 3) * 0.80
        assert accumulator.get_yield_factor() == pytest.approx(expected_factor, rel=1e-4)

class TestUtilityMethods:
    """Test utility methods."""
    
    def test_reset(self):
        """Test that reset returns accumulator to initial state."""
        accumulator = YieldImpactAccumulator()
        
        # Add some impacts
        stress = {"high_temp": 0.10, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        for _ in range(5):
            accumulator.accumulate_daily_impact(stress)
        
        # Verify impact was accumulated
        assert accumulator.get_yield_factor() < 1.0
        
        # Reset
        accumulator.reset()
        
        # Verify back to initial state
        assert accumulator.get_yield_factor() == 1.0
        assert accumulator.get_yield_loss_percentage() == 0.0
    
    def test_repr(self):
        """Test string representation."""
        accumulator = YieldImpactAccumulator()
        repr_str = repr(accumulator)
        
        assert "YieldImpactAccumulator" in repr_str
        assert "yield_factor" in repr_str
        assert "yield_loss" in repr_str

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_yield_floor(self):
        """Test that yield factor cannot go below zero."""
        accumulator = YieldImpactAccumulator()
        
        # Extreme stress (100% impact)
        total_loss = {"high_temp": 1.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        accumulator.accumulate_daily_impact(total_loss)
        
        # Should be floored at 0.0
        assert accumulator.get_yield_factor() == 0.0
        assert accumulator.get_yield_loss_percentage() == 100.0
    
    def test_empty_impacts_dict(self):
        """Test handling of empty impacts dictionary."""
        accumulator = YieldImpactAccumulator()
        empty_impacts = {}
        
        accumulator.accumulate_daily_impact(empty_impacts)
        
        # Should remain unchanged
        assert accumulator.get_yield_factor() == 1.0

class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_typical_rice_growing_season(self):
        """Test realistic rice growing season with various stresses."""
        accumulator = YieldImpactAccumulator()
        
        # Germination (15 days): Occasional low temp (2 days with 8% impact)
        for _ in range(13):
            accumulator.accumulate_daily_impact({"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0})
        for _ in range(2):
            accumulator.accumulate_daily_impact({"high_temp": 0.0, "low_temp": 0.08, "frost": 0.0, "sterility": 0.0})
        
        # Vegetative (50 days): Mostly optimal, 3 days high temp (5% impact)
        for _ in range(47):
            accumulator.accumulate_daily_impact({"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0})
        for _ in range(3):
            accumulator.accumulate_daily_impact({"high_temp": 0.05, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0})
        
        # Flowering (10 days): Critical period with 2 days sterility risk (20% impact)
        for _ in range(8):
            accumulator.accumulate_daily_impact({"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0})
        for _ in range(2):
            accumulator.accumulate_daily_impact({"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.20})
        
        # Maturation (35 days): Optimal conditions
        for _ in range(35):
            accumulator.accumulate_daily_impact({"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0})
        
        yield_factor = accumulator.get_yield_factor()
        
        # Expected: (0.92^2) * (0.95^3) * (0.80^2) ≈ 0.5928
        # Low temp: 0.92^2 = 0.8464
        # High temp: 0.95^3 = 0.857375
        # Sterility: 0.80^2 = 0.64
        # Total: 0.8464 * 0.857375 * 0.64 ≈ 0.4645
        assert 0.40 <= yield_factor <= 0.50
        assert accumulator.get_yield_loss_percentage() >= 50.0
