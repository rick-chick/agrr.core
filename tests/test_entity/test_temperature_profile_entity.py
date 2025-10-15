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
        """Test high temperature stress impact."""
        weather = WeatherData(
            time=datetime(2024, 7, 15),
            temperature_2m_mean=36.0,  # Above high_stress_threshold (35)
            temperature_2m_max=38.0,
            temperature_2m_min=33.0,
        )
        
        impacts = rice_temperature_profile.calculate_daily_stress_impacts(weather)
        
        assert impacts["high_temp"] == 0.05  # 5% impact
        assert impacts["low_temp"] == 0.0
        assert impacts["frost"] == 0.0
        # Note: sterility_risk_threshold is 35, so max=38 triggers it
        assert impacts["sterility"] == 0.20  # 20% impact
    
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
        """Test sterility risk impact during flowering."""
        weather = WeatherData(
            time=datetime(2024, 7, 20),
            temperature_2m_mean=33.0,
            temperature_2m_max=37.0,  # Above sterility_risk_threshold (35)
            temperature_2m_min=29.0,
        )
        
        impacts = rice_temperature_profile.calculate_daily_stress_impacts(weather)
        
        assert impacts["high_temp"] == 0.0  # Mean is below 35
        assert impacts["low_temp"] == 0.0
        assert impacts["frost"] == 0.0
        assert impacts["sterility"] == 0.20  # 20% impact
    
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
        """Test that custom impact rates can be specified."""
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
        
        assert impacts["high_temp"] == 0.10
        assert impacts["sterility"] == 0.30
    
    def test_no_sterility_threshold(self, wheat_temperature_profile):
        """Test that missing sterility threshold results in no sterility impact."""
        weather = WeatherData(
            time=datetime(2024, 6, 15),
            temperature_2m_mean=31.0,  # Above wheat's high_stress_threshold (30)
            temperature_2m_max=40.0,  # Very high, but no threshold set
            temperature_2m_min=25.0,
        )
        
        impacts = wheat_temperature_profile.calculate_daily_stress_impacts(weather)
        
        # Wheat should have high temp stress but no sterility impact
        assert impacts["high_temp"] == 0.05
        assert impacts["sterility"] == 0.0


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

