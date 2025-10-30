"""Tests for TemperatureProfile entity.

Tests the temperature threshold judgments and daily stress impact calculations.
"""

import pytest
from datetime import datetime

from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.weather_entity import WeatherData

@pytest.fixture
def rice_temperature_profile():
    """Temperature profile for rice (typical values)."""
    return TemperatureProfile(
        base_temperature=10.0,
        optimal_min=25.0,
        optimal_max=30.0,
        low_stress_threshold=17.0,
        high_stress_threshold=35.0,
        frost_threshold=5.0,
        max_temperature=42.0,
        sterility_risk_threshold=35.0,
    )

@pytest.fixture
def wheat_temperature_profile():
    """Temperature profile for wheat (typical values)."""
    return TemperatureProfile(
        base_temperature=0.0,
        optimal_min=15.0,
        optimal_max=24.0,
        low_stress_threshold=5.0,
        high_stress_threshold=30.0,
        frost_threshold=-5.0,
        max_temperature=35.0,
        sterility_risk_threshold=None,
    )

@pytest.fixture
def tomato_temperature_profile():
    """Temperature profile for tomato (typical values)."""
    return TemperatureProfile(
        base_temperature=10.0,
        optimal_min=20.0,
        optimal_max=26.0,
        low_stress_threshold=12.0,
        high_stress_threshold=32.0,
        frost_threshold=0.0,
        max_temperature=40.0,
        sterility_risk_threshold=35.0,
    )

class TestTemperatureJudgments:
    """Test temperature judgment methods."""
    
    def test_is_ok_temperature_within_optimal(self, rice_temperature_profile):
        """Test that temperature within optimal range returns True."""
        assert rice_temperature_profile.is_ok_temperature(27.0) is True
        assert rice_temperature_profile.is_ok_temperature(25.0) is True
        assert rice_temperature_profile.is_ok_temperature(30.0) is True
    
    def test_is_ok_temperature_outside_optimal(self, rice_temperature_profile):
        """Test that temperature outside optimal range returns False."""
        assert rice_temperature_profile.is_ok_temperature(20.0) is False
        assert rice_temperature_profile.is_ok_temperature(35.0) is False
    
    def test_is_ok_temperature_none(self, rice_temperature_profile):
        """Test that None temperature returns False."""
        assert rice_temperature_profile.is_ok_temperature(None) is False
    
    def test_is_low_temp_stress(self, rice_temperature_profile):
        """Test low temperature stress detection."""
        assert rice_temperature_profile.is_low_temp_stress(16.0) is True
        assert rice_temperature_profile.is_low_temp_stress(17.0) is False
        assert rice_temperature_profile.is_low_temp_stress(20.0) is False
    
    def test_is_high_temp_stress(self, rice_temperature_profile):
        """Test high temperature stress detection."""
        assert rice_temperature_profile.is_high_temp_stress(36.0) is True
        assert rice_temperature_profile.is_high_temp_stress(35.0) is False
        assert rice_temperature_profile.is_high_temp_stress(30.0) is False
    
    def test_is_frost_risk(self, rice_temperature_profile):
        """Test frost risk detection."""
        assert rice_temperature_profile.is_frost_risk(4.0) is True
        assert rice_temperature_profile.is_frost_risk(5.0) is True
        assert rice_temperature_profile.is_frost_risk(6.0) is False
    
    def test_is_sterility_risk(self, rice_temperature_profile):
        """Test sterility risk detection."""
        assert rice_temperature_profile.is_sterility_risk(35.0) is True
        assert rice_temperature_profile.is_sterility_risk(36.0) is True
        assert rice_temperature_profile.is_sterility_risk(34.0) is False
    
    def test_is_sterility_risk_none_threshold(self, wheat_temperature_profile):
        """Test sterility risk returns False when threshold is None."""
        assert wheat_temperature_profile.is_sterility_risk(40.0) is False

class TestDailyGDD:
    """Test daily GDD calculations."""
    
    def test_daily_gdd_optimal_range(self, rice_temperature_profile):
        """Test GDD calculation within optimal range."""
        # T_mean = 27°C, base = 10°C → GDD = 17°C
        # Efficiency = 1.0 (optimal range)
        gdd = rice_temperature_profile.daily_gdd(27.0)
        assert abs(gdd - 17.0) < 0.01
    
    def test_daily_gdd_sub_optimal_cool(self, rice_temperature_profile):
        """Test GDD calculation in sub-optimal (cool) range."""
        # T_mean = 15°C, base = 10°C, optimal_min = 25°C
        # Base GDD = 5°C
        # Efficiency = (15 - 10) / (25 - 10) = 5/15 = 0.333
        # Modified GDD = 5 * 0.333 = 1.667
        gdd = rice_temperature_profile.daily_gdd(15.0)
        expected = 5.0 * (5.0 / 15.0)
        assert abs(gdd - expected) < 0.01
    
    def test_daily_gdd_sub_optimal_warm(self, rice_temperature_profile):
        """Test GDD calculation in sub-optimal (warm) range."""
        # T_mean = 35°C, base = 10°C, optimal_max = 30°C, max = 42°C
        # Base GDD = 25°C
        # Efficiency = (42 - 35) / (42 - 30) = 7/12 = 0.583
        # Modified GDD = 25 * 0.583 = 14.583
        gdd = rice_temperature_profile.daily_gdd(35.0)
        expected = 25.0 * (7.0 / 12.0)
        assert abs(gdd - expected) < 0.01
    
    def test_daily_gdd_below_base(self, rice_temperature_profile):
        """Test GDD is zero below base temperature."""
        gdd = rice_temperature_profile.daily_gdd(5.0)
        assert gdd == 0.0
    
    def test_daily_gdd_above_max(self, rice_temperature_profile):
        """Test GDD is zero above max temperature."""
        gdd = rice_temperature_profile.daily_gdd(43.0)
        assert gdd == 0.0
    
    def test_daily_gdd_none(self, rice_temperature_profile):
        """Test GDD is zero for None temperature."""
        gdd = rice_temperature_profile.daily_gdd(None)
        assert gdd == 0.0

class TestCalculateDailyStressImpacts:
    """Test calculate_daily_stress_impacts method."""
    
    def test_no_stress(self, rice_temperature_profile):
        """Test that optimal conditions result in no stress impacts."""
        weather = WeatherData(
            time=datetime(2024, 7, 15),
            temperature_2m_mean=27.0,  # Optimal
            temperature_2m_max=29.0,   # Below sterility
            temperature_2m_min=24.0,   # Above frost
        )
        
        impacts = rice_temperature_profile.calculate_daily_stress_impacts(weather)
        
        assert impacts["high_temp"] == 0.0
        assert impacts["low_temp"] == 0.0
        assert impacts["frost"] == 0.0
        assert impacts["sterility"] == 0.0
    
    def test_high_temp_stress_only(self, rice_temperature_profile):
        """Test high temperature stress impact.
        
        Note: This test now includes GDD efficiency-based attenuation.
        Mean temp = 36°C is sub-optimal (optimal_max=30°C), so efficiency is low.
        """
        weather = WeatherData(
            time=datetime(2024, 7, 15),
            temperature_2m_mean=36.0,  # Above high_stress_threshold (35)
            temperature_2m_max=38.0,
            temperature_2m_min=33.0,
        )
        
        impacts = rice_temperature_profile.calculate_daily_stress_impacts(weather)
        
        # Calculate expected values with attenuation
        # Mean temp efficiency: (42 - 36) / (42 - 30) = 6/12 = 0.5
        # Base impact: 0.05 * (38-35)/(38-33) = 0.05 * 3/5 = 0.03
        # Attenuation factor: 1 - (0.5 * 0.7) = 1 - 0.35 = 0.65
        # Expected impact: 0.03 * 0.65 = 0.0195
        mean_temp_efficiency = (42.0 - 36.0) / (42.0 - 30.0)
        stress_proportion = (38.0 - 35.0) / (38.0 - 33.0)
        base_impact = 0.05 * stress_proportion
        attenuation_factor = 1.0 - (mean_temp_efficiency * 0.7)
        expected_high_temp = base_impact * attenuation_factor
        
        assert abs(impacts["high_temp"] - expected_high_temp) < 0.001
        assert impacts["low_temp"] == 0.0
        assert impacts["frost"] == 0.0
        # Note: sterility_risk_threshold is 35, so max=38 triggers it
        assert impacts["sterility"] == 0.20  # 20% impact (no attenuation)
    
    def test_low_temp_stress_only(self, rice_temperature_profile):
        """Test low temperature stress impact."""
        weather = WeatherData(
            time=datetime(2024, 4, 15),
            temperature_2m_mean=15.0,  # Below low_stress_threshold (17)
            temperature_2m_max=18.0,
            temperature_2m_min=12.0,
        )
        
        impacts = rice_temperature_profile.calculate_daily_stress_impacts(weather)
        
        assert impacts["high_temp"] == 0.0
        assert impacts["low_temp"] == 0.08  # 8% impact
        assert impacts["frost"] == 0.0
        assert impacts["sterility"] == 0.0
    
    def test_frost_risk(self, rice_temperature_profile):
        """Test frost risk impact."""
        weather = WeatherData(
            time=datetime(2024, 3, 15),
            temperature_2m_mean=8.0,
            temperature_2m_max=12.0,
            temperature_2m_min=3.0,  # Below frost_threshold (5)
        )
        
        impacts = rice_temperature_profile.calculate_daily_stress_impacts(weather)
        
        assert impacts["high_temp"] == 0.0
        assert impacts["low_temp"] == 0.08  # Also low temp stress
        assert impacts["frost"] == 0.15  # 15% impact
        assert impacts["sterility"] == 0.0
    
    def test_sterility_risk(self, rice_temperature_profile):
        """Test sterility risk impact during flowering.
        
        Note: GDD efficiency-based attenuation applies to high_temp stress.
        Mean temp = 33°C is sub-optimal but still has some efficiency.
        """
        weather = WeatherData(
            time=datetime(2024, 7, 20),
            temperature_2m_mean=33.0,
            temperature_2m_max=37.0,  # Above sterility_risk_threshold (35) and high_stress_threshold (35)
            temperature_2m_min=29.0,
        )
        
        impacts = rice_temperature_profile.calculate_daily_stress_impacts(weather)
        
        # Calculate expected high_temp with attenuation
        # Mean temp efficiency: (42 - 33) / (42 - 30) = 9/12 = 0.75
        # Base impact: 0.05 * (37-35)/(37-29) = 0.05 * 2/8 = 0.0125
        # Attenuation factor: 1 - (0.75 * 0.7) = 1 - 0.525 = 0.475
        # Expected: 0.0125 * 0.475 = 0.0059375
        mean_temp_efficiency = (42.0 - 33.0) / (42.0 - 30.0)
        stress_proportion = (37.0 - 35.0) / (37.0 - 29.0)
        base_impact = 0.05 * stress_proportion
        attenuation_factor = 1.0 - (mean_temp_efficiency * 0.7)
        expected_high_temp = base_impact * attenuation_factor
        
        assert abs(impacts["high_temp"] - expected_high_temp) < 0.001
        assert impacts["low_temp"] == 0.0
        assert impacts["frost"] == 0.0
        assert impacts["sterility"] == 0.20  # 20% impact (no attenuation)
    
    def test_multiple_stress_types(self, rice_temperature_profile):
        """Test multiple stress types occurring simultaneously."""
        weather = WeatherData(
            time=datetime(2024, 3, 10),
            temperature_2m_mean=10.0,  # Below low_stress_threshold
            temperature_2m_max=15.0,
            temperature_2m_min=2.0,  # Below frost_threshold
        )
        
        impacts = rice_temperature_profile.calculate_daily_stress_impacts(weather)
        
        assert impacts["high_temp"] == 0.0
        assert impacts["low_temp"] == 0.08  # Low temp stress
        assert impacts["frost"] == 0.15     # Frost risk
        assert impacts["sterility"] == 0.0
    
    def test_custom_impact_rates(self):
        """Test that custom impact rates can be specified.
        
        Note: Custom impact rates are subject to GDD efficiency-based attenuation.
        """
        profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=25.0,
            low_stress_threshold=15.0,
            high_stress_threshold=30.0,
            frost_threshold=0.0,
            max_temperature=35.0,
            sterility_risk_threshold=32.0,
            # Custom impact rates
            high_temp_daily_impact=0.10,  # 10% instead of 5%
            low_temp_daily_impact=0.12,   # 12% instead of 8%
            frost_daily_impact=0.25,      # 25% instead of 15%
            sterility_daily_impact=0.30,  # 30% instead of 20%
        )
        
        weather = WeatherData(
            time=datetime(2024, 7, 15),
            temperature_2m_mean=31.0,  # High temp stress
            temperature_2m_max=33.0,   # Sterility risk
            temperature_2m_min=28.0,
        )
        
        impacts = profile.calculate_daily_stress_impacts(weather)
        
        # Calculate expected high_temp with attenuation
        # Mean temp efficiency: (35 - 31) / (35 - 25) = 4/10 = 0.4
        # Base impact: 0.10 * (33-30)/(33-28) = 0.10 * 3/5 = 0.06
        # Attenuation factor: 1 - (0.4 * 0.7) = 1 - 0.28 = 0.72
        # Expected: 0.06 * 0.72 = 0.0432
        mean_temp_efficiency = (35.0 - 31.0) / (35.0 - 25.0)
        stress_proportion = (33.0 - 30.0) / (33.0 - 28.0)
        base_impact = 0.10 * stress_proportion
        attenuation_factor = 1.0 - (mean_temp_efficiency * 0.7)
        expected_high_temp = base_impact * attenuation_factor
        
        assert abs(impacts["high_temp"] - expected_high_temp) < 0.001
        assert impacts["sterility"] == 0.30  # No attenuation for sterility
    
    def test_no_sterility_threshold(self, wheat_temperature_profile):
        """Test that missing sterility threshold results in no sterility impact."""
        weather = WeatherData(
            time=datetime(2024, 6, 15),
            temperature_2m_mean=31.0,  # Above wheat's high_stress_threshold (30)
            temperature_2m_max=40.0,  # Very high, but no threshold set
            temperature_2m_min=25.0,
        )
        
        impacts = wheat_temperature_profile.calculate_daily_stress_impacts(weather)
        
        # Calculate expected with attenuation
        # Mean temp efficiency: (35 - 31) / (35 - 24) = 4/11 = 0.364
        # Base impact: 0.05 * (40-30)/(40-25) = 0.05 * 10/15 = 0.0333
        # Attenuation factor: 1 - (0.364 * 0.7) = 1 - 0.255 = 0.745
        # Expected: 0.0333 * 0.745 = 0.0248
        mean_temp_efficiency = (35.0 - 31.0) / (35.0 - 24.0)
        stress_proportion = (40.0 - 30.0) / (40.0 - 25.0)
        base_impact = 0.05 * stress_proportion
        attenuation_factor = 1.0 - (mean_temp_efficiency * 0.7)
        expected_high_temp = base_impact * attenuation_factor
        
        assert abs(impacts["high_temp"] - expected_high_temp) < 0.001
        assert impacts["sterility"] == 0.0

class TestGDDEfficiencyBasedAttenuation:
    """Test GDD efficiency-based stress attenuation feature."""
    
    def test_tomato_summer_optimal_mean_temp(self, tomato_temperature_profile):
        """Test tomato in summer with optimal mean temp but brief high peaks.
        
        Scenario: Summer day with mean=24°C (optimal), max=38°C (brief peak)
        Expected: Stress impact should be significantly attenuated
        because mean temperature is within optimal range.
        """
        weather = WeatherData(
            time=datetime(2024, 8, 10),
            temperature_2m_mean=24.0,  # Optimal (20-26°C)
            temperature_2m_max=38.0,   # Peak exceeds high_stress_threshold (32°C)
            temperature_2m_min=18.0,
        )
        
        impacts = tomato_temperature_profile.calculate_daily_stress_impacts(weather)
        
        # Calculate expected values
        # Mean temp efficiency: 1.0 (in optimal range 20-26°C)
        # Base impact: 0.05 * (38-32)/(38-18) = 0.05 * 6/20 = 0.015
        # Attenuation factor: 1 - (1.0 * 0.7) = 0.3
        # Expected impact: 0.015 * 0.3 = 0.0045 (70% reduction!)
        mean_temp_efficiency = 1.0  # Optimal range
        stress_proportion = (38.0 - 32.0) / (38.0 - 18.0)
        base_impact = 0.05 * stress_proportion
        attenuation_factor = 1.0 - (mean_temp_efficiency * 0.7)
        expected_high_temp = base_impact * attenuation_factor
        
        assert abs(impacts["high_temp"] - expected_high_temp) < 0.001
        # Verify significant attenuation occurred
        assert impacts["high_temp"] < 0.01  # Less than 1% impact
        assert impacts["low_temp"] == 0.0
        assert impacts["frost"] == 0.0
    
    def test_tomato_summer_sub_optimal_mean_temp(self, tomato_temperature_profile):
        """Test tomato in extreme summer with sub-optimal mean temp.
        
        Scenario: Extreme summer day with mean=32°C (sub-optimal), max=38°C
        Expected: Less attenuation because mean temp is also high.
        """
        weather = WeatherData(
            time=datetime(2024, 8, 15),
            temperature_2m_mean=32.0,  # Sub-optimal (above optimal_max=26°C)
            temperature_2m_max=38.0,   # Peak exceeds high_stress_threshold
            temperature_2m_min=26.0,
        )
        
        impacts = tomato_temperature_profile.calculate_daily_stress_impacts(weather)
        
        # Calculate expected values
        # Mean temp efficiency: (40 - 32) / (40 - 26) = 8/14 = 0.571
        # Base impact: 0.05 * (38-32)/(38-26) = 0.05 * 6/12 = 0.025
        # Attenuation factor: 1 - (0.571 * 0.7) = 1 - 0.4 = 0.6
        # Expected impact: 0.025 * 0.6 = 0.015
        mean_temp_efficiency = (40.0 - 32.0) / (40.0 - 26.0)
        stress_proportion = (38.0 - 32.0) / (38.0 - 26.0)
        base_impact = 0.05 * stress_proportion
        attenuation_factor = 1.0 - (mean_temp_efficiency * 0.7)
        expected_high_temp = base_impact * attenuation_factor
        
        assert abs(impacts["high_temp"] - expected_high_temp) < 0.001
        # Verify moderate attenuation (less than optimal case)
        assert impacts["high_temp"] > 0.01  # More than 1% impact
        assert impacts["high_temp"] < 0.02  # But still attenuated
    
    def test_tomato_extreme_heat_no_attenuation(self, tomato_temperature_profile):
        """Test tomato in extreme heat with very high mean temp.
        
        Scenario: Extreme heat wave with mean=38°C, max=42°C
        Expected: Minimal attenuation because day is overall stressful.
        """
        weather = WeatherData(
            time=datetime(2024, 8, 20),
            temperature_2m_mean=38.0,  # Very high (approaching max_temperature=40°C)
            temperature_2m_max=42.0,   # Above max_temperature
            temperature_2m_min=34.0,
        )
        
        impacts = tomato_temperature_profile.calculate_daily_stress_impacts(weather)
        
        # Calculate expected values
        # Mean temp efficiency: (40 - 38) / (40 - 26) = 2/14 = 0.143
        # Base impact: 0.05 * (42-32)/(42-34) = 0.05 * 10/8 = 0.0625 (capped at stress_proportion=1.0)
        # Note: max_temperature check happens in is_high_temp_stress (uses max temp)
        # stress_proportion: (42-32)/(42-34) = 10/8 = 1.25 → capped to 1.0
        # Base impact: 0.05 * 1.0 = 0.05
        # Attenuation factor: 1 - (0.143 * 0.7) = 1 - 0.1 = 0.9
        # Expected impact: 0.05 * 0.9 = 0.045
        mean_temp_efficiency = (40.0 - 38.0) / (40.0 - 26.0)
        stress_proportion = min(1.0, (42.0 - 32.0) / (42.0 - 34.0))
        base_impact = 0.05 * stress_proportion
        attenuation_factor = 1.0 - (mean_temp_efficiency * 0.7)
        expected_high_temp = base_impact * attenuation_factor
        
        assert abs(impacts["high_temp"] - expected_high_temp) < 0.001
        # Verify minimal attenuation (near full impact)
        assert impacts["high_temp"] > 0.04  # Close to full 5% impact
    
    def test_comparison_old_vs_new_tomato(self, tomato_temperature_profile):
        """Compare old (no attenuation) vs new (GDD-based attenuation) for tomato.
        
        This test demonstrates the improvement for tomato in summer.
        """
        # Summer day: optimal mean, but brief afternoon peak
        weather = WeatherData(
            time=datetime(2024, 7, 25),
            temperature_2m_mean=23.0,  # Optimal
            temperature_2m_max=36.0,   # Brief peak
            temperature_2m_min=16.0,
        )
        
        impacts = tomato_temperature_profile.calculate_daily_stress_impacts(weather)
        
        # OLD calculation (without attenuation):
        # stress_proportion = (36-32)/(36-16) = 4/20 = 0.2
        # old_impact = 0.05 * 0.2 = 0.01 (1% yield loss per day)
        
        # NEW calculation (with attenuation):
        # mean_temp_efficiency = 1.0 (optimal)
        # attenuation_factor = 1 - (1.0 * 0.7) = 0.3
        # new_impact = 0.01 * 0.3 = 0.003 (0.3% yield loss per day)
        
        old_impact_estimate = 0.05 * ((36.0 - 32.0) / (36.0 - 16.0))
        
        # New impact should be significantly lower
        assert impacts["high_temp"] < old_impact_estimate * 0.4  # At least 60% reduction
        assert impacts["high_temp"] < 0.005  # Less than 0.5% impact

class TestTemperatureProfileImmutability:
    """Test that TemperatureProfile is immutable (frozen dataclass)."""
    
    def test_cannot_modify_fields(self, rice_temperature_profile):
        """Test that fields cannot be modified after creation."""
        with pytest.raises(Exception):  # FrozenInstanceError
            rice_temperature_profile.base_temperature = 15.0
    
    def test_cannot_modify_impact_rates(self, rice_temperature_profile):
        """Test that impact rates cannot be modified after creation."""
        with pytest.raises(Exception):  # FrozenInstanceError
            rice_temperature_profile.high_temp_daily_impact = 0.10

