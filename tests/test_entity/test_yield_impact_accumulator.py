"""Tests for YieldImpactAccumulator value object.

Tests the accumulation of daily stress impacts and yield factor calculation.
"""

import pytest

from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.value_objects.yield_impact_accumulator import (
    YieldImpactAccumulator,
    StressSensitivity,
    DEFAULT_STAGE_SENSITIVITIES,
)


class TestStressSensitivity:
    """Test StressSensitivity value object."""
    
    def test_default_values(self):
        """Test that default sensitivity values are valid."""
        sensitivity = StressSensitivity()
        assert sensitivity.high_temp == 0.5
        assert sensitivity.low_temp == 0.5
        assert sensitivity.frost == 0.7
        assert sensitivity.sterility == 0.9
    
    def test_custom_values(self):
        """Test creating sensitivity with custom values."""
        sensitivity = StressSensitivity(
            high_temp=0.9,
            low_temp=0.8,
            frost=0.6,
            sterility=1.0,
        )
        assert sensitivity.high_temp == 0.9
        assert sensitivity.low_temp == 0.8
        assert sensitivity.frost == 0.6
        assert sensitivity.sterility == 1.0
    
    def test_validation_rejects_negative(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            StressSensitivity(high_temp=-0.1)
    
    def test_validation_rejects_above_one(self):
        """Test that values above 1 are rejected."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            StressSensitivity(low_temp=1.5)
    
    def test_immutability(self):
        """Test that StressSensitivity is immutable."""
        sensitivity = StressSensitivity()
        with pytest.raises(Exception):  # FrozenInstanceError
            sensitivity.high_temp = 0.9


class TestDefaultStageSensitivities:
    """Test default stage sensitivity configuration."""
    
    def test_germination_low_sensitivity(self):
        """Test that germination has low sensitivity."""
        sens = DEFAULT_STAGE_SENSITIVITIES["germination"]
        assert sens.high_temp == 0.2
        assert sens.low_temp == 0.3
        assert sens.sterility == 0.0  # No sterility risk during germination
    
    def test_flowering_high_sensitivity(self):
        """Test that flowering has highest sensitivity."""
        sens = DEFAULT_STAGE_SENSITIVITIES["flowering"]
        assert sens.high_temp == 0.9
        assert sens.low_temp == 0.9
        assert sens.frost == 0.9
        assert sens.sterility == 1.0  # Maximum sterility sensitivity
    
    def test_all_stages_present(self):
        """Test that all expected stages are configured."""
        expected_stages = [
            "germination",
            "vegetative",
            "flowering",
            "heading",
            "grain_filling",
            "ripening",
            "maturation",
        ]
        for stage in expected_stages:
            assert stage in DEFAULT_STAGE_SENSITIVITIES


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
        stage = GrowthStage(name="flowering", order=3)
        
        # No stress impacts
        daily_impacts = {
            "high_temp": 0.0,
            "low_temp": 0.0,
            "frost": 0.0,
            "sterility": 0.0,
        }
        
        # Accumulate for 5 days
        for _ in range(5):
            accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        assert accumulator.get_yield_factor() == 1.0
        assert accumulator.get_yield_loss_percentage() == 0.0
    
    def test_repr(self):
        """Test string representation."""
        accumulator = YieldImpactAccumulator()
        repr_str = repr(accumulator)
        assert "YieldImpactAccumulator" in repr_str
        assert "yield_factor=1.000" in repr_str
        assert "yield_loss=0.0%" in repr_str


class TestYieldImpactAccumulation:
    """Test yield impact accumulation logic."""
    
    def test_single_day_high_temp_stress(self):
        """Test single day of high temperature stress."""
        accumulator = YieldImpactAccumulator()
        stage = GrowthStage(name="flowering", order=3)
        
        # High temp stress: 5% impact, flowering sensitivity = 0.9
        daily_impacts = {
            "high_temp": 0.05,
            "low_temp": 0.0,
            "frost": 0.0,
            "sterility": 0.0,
        }
        
        accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        # Expected: 1.0 - (0.05 * 0.9) = 0.955
        expected = 1.0 - (0.05 * 0.9)
        assert abs(accumulator.get_yield_factor() - expected) < 0.001
        assert abs(accumulator.get_yield_loss_percentage() - 4.5) < 0.1
    
    def test_multiple_days_same_stress(self):
        """Test multiple days of the same stress type."""
        accumulator = YieldImpactAccumulator()
        stage = GrowthStage(name="flowering", order=3)
        
        # High temp stress for 3 days
        daily_impacts = {
            "high_temp": 0.05,
            "low_temp": 0.0,
            "frost": 0.0,
            "sterility": 0.0,
        }
        
        for _ in range(3):
            accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        # Expected: (1 - 0.05*0.9)^3 = 0.955^3 ≈ 0.870
        daily_factor = 1.0 - (0.05 * 0.9)
        expected = daily_factor ** 3
        assert abs(accumulator.get_yield_factor() - expected) < 0.001
    
    def test_multiple_stress_types_same_day(self):
        """Test multiple stress types occurring on the same day."""
        accumulator = YieldImpactAccumulator()
        stage = GrowthStage(name="vegetative", order=2)
        
        # Both high temp and low temp stress (unusual but possible)
        daily_impacts = {
            "high_temp": 0.05,  # 5% impact
            "low_temp": 0.08,   # 8% impact
            "frost": 0.0,
            "sterility": 0.0,
        }
        
        accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        # Vegetative sensitivities: high_temp=0.3, low_temp=0.2
        # High temp: 1 - (0.05 * 0.3) = 0.985
        # Low temp: 1 - (0.08 * 0.2) = 0.984
        # Combined: 0.985 * 0.984 ≈ 0.969
        expected = (1.0 - 0.05 * 0.3) * (1.0 - 0.08 * 0.2)
        assert abs(accumulator.get_yield_factor() - expected) < 0.001
    
    def test_sterility_risk_severe_impact(self):
        """Test that sterility risk has severe impact during flowering."""
        accumulator = YieldImpactAccumulator()
        stage = GrowthStage(name="flowering", order=3)
        
        # Sterility risk: 20% impact, flowering sensitivity = 1.0
        daily_impacts = {
            "high_temp": 0.0,
            "low_temp": 0.0,
            "frost": 0.0,
            "sterility": 0.20,
        }
        
        accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        # Expected: 1.0 - (0.20 * 1.0) = 0.80 (20% yield loss)
        assert abs(accumulator.get_yield_factor() - 0.80) < 0.001
        assert abs(accumulator.get_yield_loss_percentage() - 20.0) < 0.1
    
    def test_frost_during_germination(self):
        """Test frost impact during germination."""
        accumulator = YieldImpactAccumulator()
        stage = GrowthStage(name="germination", order=1)
        
        # Frost: 15% impact, germination sensitivity = 0.5
        daily_impacts = {
            "high_temp": 0.0,
            "low_temp": 0.0,
            "frost": 0.15,
            "sterility": 0.0,
        }
        
        accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        # Expected: 1.0 - (0.15 * 0.5) = 0.925
        expected = 1.0 - (0.15 * 0.5)
        assert abs(accumulator.get_yield_factor() - expected) < 0.001


class TestStageSensitivityMatching:
    """Test flexible stage name matching."""
    
    def test_exact_match(self):
        """Test exact stage name match."""
        accumulator = YieldImpactAccumulator()
        stage = GrowthStage(name="flowering", order=3)
        
        sensitivity = accumulator._get_sensitivity("flowering")
        assert sensitivity.high_temp == 0.9
    
    def test_case_insensitive_match(self):
        """Test case-insensitive matching."""
        accumulator = YieldImpactAccumulator()
        
        sensitivity = accumulator._get_sensitivity("FLOWERING")
        assert sensitivity.high_temp == 0.9
    
    def test_space_normalization(self):
        """Test that spaces are normalized to underscores."""
        accumulator = YieldImpactAccumulator()
        
        sensitivity = accumulator._get_sensitivity("grain filling")
        assert sensitivity.high_temp == 0.7
    
    def test_partial_match(self):
        """Test partial substring matching."""
        accumulator = YieldImpactAccumulator()
        
        # "Grain Filling Stage" should match "grain_filling"
        sensitivity = accumulator._get_sensitivity("Grain Filling Stage")
        assert sensitivity.high_temp == 0.7
    
    def test_unknown_stage_fallback(self):
        """Test that unknown stages fall back to moderate sensitivity."""
        accumulator = YieldImpactAccumulator()
        
        sensitivity = accumulator._get_sensitivity("unknown_stage")
        assert sensitivity.high_temp == 0.5
        assert sensitivity.low_temp == 0.5
        assert sensitivity.frost == 0.7
        assert sensitivity.sterility == 0.5


class TestYieldImpactAccumulatorAdvanced:
    """Test advanced accumulator features."""
    
    def test_reset(self):
        """Test that reset returns accumulator to initial state."""
        accumulator = YieldImpactAccumulator()
        stage = GrowthStage(name="flowering", order=3)
        
        # Apply some stress
        daily_impacts = {"high_temp": 0.10, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        # Verify impact was recorded
        assert accumulator.get_yield_factor() < 1.0
        
        # Reset
        accumulator.reset()
        
        # Verify reset to initial state
        assert accumulator.get_yield_factor() == 1.0
        assert accumulator.get_yield_loss_percentage() == 0.0
    
    def test_severe_cumulative_stress(self):
        """Test severe cumulative stress over many days."""
        accumulator = YieldImpactAccumulator()
        stage = GrowthStage(name="flowering", order=3)
        
        # Moderate stress for 20 days
        daily_impacts = {"high_temp": 0.05, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        
        for _ in range(20):
            accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        # Expected: (1 - 0.05*0.9)^20 = 0.955^20 ≈ 0.389 (61% yield loss)
        daily_factor = 1.0 - (0.05 * 0.9)
        expected = daily_factor ** 20
        assert abs(accumulator.get_yield_factor() - expected) < 0.01
        assert accumulator.get_yield_loss_percentage() > 60.0
    
    def test_stages_with_different_sensitivities(self):
        """Test accumulation across stages with different sensitivities."""
        accumulator = YieldImpactAccumulator()
        
        # Germination: low sensitivity
        germination = GrowthStage(name="germination", order=1)
        daily_impacts = {"high_temp": 0.05, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        accumulator.accumulate_daily_impact(germination, daily_impacts)
        factor_after_germination = accumulator.get_yield_factor()
        
        # Flowering: high sensitivity
        flowering = GrowthStage(name="flowering", order=3)
        accumulator.accumulate_daily_impact(flowering, daily_impacts)
        factor_after_flowering = accumulator.get_yield_factor()
        
        # Flowering should have larger impact
        germination_impact = 1.0 - factor_after_germination
        flowering_impact = factor_after_germination - factor_after_flowering
        assert flowering_impact > germination_impact
    
    def test_yield_factor_never_negative(self):
        """Test that yield factor is clamped at 0.0."""
        accumulator = YieldImpactAccumulator()
        stage = GrowthStage(name="flowering", order=3)
        
        # Extreme stress for many days (should cap at 0)
        daily_impacts = {"high_temp": 0.50, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        
        for _ in range(10):
            accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        # Should be clamped at 0.0, not negative
        assert accumulator.get_yield_factor() >= 0.0
        assert accumulator.get_yield_loss_percentage() <= 100.0
    
    def test_custom_stage_sensitivities(self):
        """Test using custom stage sensitivities."""
        # Create custom sensitivities
        custom_sensitivities = {
            "custom_stage": StressSensitivity(
                high_temp=0.95,
                low_temp=0.85,
                frost=0.75,
                sterility=0.65,
            )
        }
        
        accumulator = YieldImpactAccumulator(stage_sensitivities=custom_sensitivities)
        stage = GrowthStage(name="custom_stage", order=1)
        
        daily_impacts = {"high_temp": 0.10, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        accumulator.accumulate_daily_impact(stage, daily_impacts)
        
        # Expected: 1.0 - (0.10 * 0.95) = 0.905
        expected = 1.0 - (0.10 * 0.95)
        assert abs(accumulator.get_yield_factor() - expected) < 0.001


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_typical_rice_growing_season(self):
        """Test typical rice growing season with mixed stress."""
        accumulator = YieldImpactAccumulator()
        
        # Germination: 5 days, no stress
        germination = GrowthStage(name="germination", order=1)
        no_stress = {"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        for _ in range(5):
            accumulator.accumulate_daily_impact(germination, no_stress)
        
        # Vegetative: 30 days, 2 days of low temp stress
        vegetative = GrowthStage(name="vegetative", order=2)
        for _ in range(28):
            accumulator.accumulate_daily_impact(vegetative, no_stress)
        low_temp_stress = {"high_temp": 0.0, "low_temp": 0.08, "frost": 0.0, "sterility": 0.0}
        for _ in range(2):
            accumulator.accumulate_daily_impact(vegetative, low_temp_stress)
        
        # Flowering: 15 days, 1 day of sterility risk
        flowering = GrowthStage(name="flowering", order=3)
        for _ in range(14):
            accumulator.accumulate_daily_impact(flowering, no_stress)
        sterility_stress = {"high_temp": 0.0, "low_temp": 0.0, "frost": 0.0, "sterility": 0.20}
        accumulator.accumulate_daily_impact(flowering, sterility_stress)
        
        # Grain filling: 30 days, 3 days of high temp stress
        grain_filling = GrowthStage(name="grain_filling", order=4)
        for _ in range(27):
            accumulator.accumulate_daily_impact(grain_filling, no_stress)
        high_temp_stress = {"high_temp": 0.05, "low_temp": 0.0, "frost": 0.0, "sterility": 0.0}
        for _ in range(3):
            accumulator.accumulate_daily_impact(grain_filling, high_temp_stress)
        
        # Result should show significant but not catastrophic loss
        yield_factor = accumulator.get_yield_factor()
        yield_loss_pct = accumulator.get_yield_loss_percentage()
        
        # Expect 25-35% total yield loss (conservative estimate)
        assert 0.65 <= yield_factor <= 0.80
        assert 20.0 <= yield_loss_pct <= 35.0

