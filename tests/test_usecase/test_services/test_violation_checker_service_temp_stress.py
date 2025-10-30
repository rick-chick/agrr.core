"""Tests for temperature stress checks in ViolationCheckerService."""

import pytest
from datetime import datetime, timedelta

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.entity.value_objects.violation_type import ViolationType
from agrr_core.usecase.services.violation_checker_service import ViolationCheckerService

class TestTemperatureStressChecks:
    """Test temperature stress violation detection."""
    
    @pytest.fixture
    def checker(self):
        """Create ViolationCheckerService instance."""
        return ViolationCheckerService()
    
    @pytest.fixture
    def field(self):
        """Create test field."""
        return Field(
            field_id="field1",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=500.0,
            fallow_period_days=28
        )
    
    @pytest.fixture
    def crop_profile(self):
        """Create crop profile with temperature profiles."""
        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=18.0,
            optimal_max=28.0,
            low_stress_threshold=15.0,
            high_stress_threshold=32.0,
            frost_threshold=0.0,
            max_temperature=35.0,
            sterility_risk_threshold=33.0
        )
        
        crop = Crop(
            crop_id="tomato",
            name="トマト",
            variety="桃太郎",
            area_per_unit=1.0
        )
        
        # Create stage requirements
        stage = GrowthStage(name="vegetative", order=1)
        sunshine_profile = SunshineProfile(
            minimum_sunshine_hours=4.0,
            target_sunshine_hours=8.0
        )
        thermal_req = ThermalRequirement(required_gdd=500.0)
        
        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=thermal_req
        )
        
        crop_profile = CropProfile(
            crop=crop,
            stage_requirements=[stage_req]
        )
        
        return crop_profile
    
    @pytest.fixture
    def allocation(self, field, crop_profile):
        """Create test allocation."""
        return CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop_profile.crop,
            start_date=datetime(2023, 6, 1),
            completion_date=datetime(2023, 7, 31),
            area_used=100.0,
            growth_days=60,
            accumulated_gdd=1200.0,
            total_cost=30000.0
        )
    
    def test_no_temperature_stress(self, checker, allocation, crop_profile):
        """Test that normal temperatures don't trigger violations."""
        # Normal temperature weather
        weather_data = [
            WeatherData(
                time=datetime(2023, 6, 1),
                temperature_2m_mean=25.0,
                temperature_2m_max=30.0,
                temperature_2m_min=20.0
            )
        ]
        
        violations = checker.check_violations(
            allocation=allocation,
            weather_data=weather_data,
            crop_profile=crop_profile
        )
        
        # Filter only temperature stress violations
        temp_violations = [
            v for v in violations 
            if v.violation_type in [
                ViolationType.HIGH_TEMP_STRESS,
                ViolationType.LOW_TEMP_STRESS,
                ViolationType.FROST_RISK,
                ViolationType.STERILITY_RISK
            ]
        ]
        
        assert len(temp_violations) == 0, "No temperature stress violations expected"
    
    def test_high_temperature_stress(self, checker, allocation, crop_profile):
        """Test detection of high temperature stress."""
        # Hot weather
        weather_data = [
            WeatherData(
                time=datetime(2023, 6, 1),
                temperature_2m_mean=25.0,
                temperature_2m_max=35.0,  # Above high_stress_threshold (32.0)
                temperature_2m_min=20.0
            )
        ]
        
        violations = checker.check_violations(
            allocation=allocation,
            weather_data=weather_data,
            crop_profile=crop_profile
        )
        
        # Filter high temp stress violations
        high_temp_violations = [
            v for v in violations 
            if v.violation_type == ViolationType.HIGH_TEMP_STRESS
        ]
        
        assert len(high_temp_violations) >= 1, "High temperature stress should be detected"
        assert high_temp_violations[0].severity == "warning"
        assert "High temperature stress" in high_temp_violations[0].message
        assert "35.0" in high_temp_violations[0].message
    
    def test_low_temperature_stress(self, checker, allocation, crop_profile):
        """Test detection of low temperature stress."""
        # Cold weather
        weather_data = [
            WeatherData(
                time=datetime(2023, 6, 1),
                temperature_2m_mean=12.0,  # Below low_stress_threshold (15.0)
                temperature_2m_max=18.0,
                temperature_2m_min=8.0
            )
        ]
        
        violations = checker.check_violations(
            allocation=allocation,
            weather_data=weather_data,
            crop_profile=crop_profile
        )
        
        # Filter low temp stress violations
        low_temp_violations = [
            v for v in violations 
            if v.violation_type == ViolationType.LOW_TEMP_STRESS
        ]
        
        assert len(low_temp_violations) >= 1, "Low temperature stress should be detected"
        assert low_temp_violations[0].severity == "warning"
        assert "Low temperature stress" in low_temp_violations[0].message
        assert "12.0" in low_temp_violations[0].message
    
    def test_frost_risk(self, checker, allocation, crop_profile):
        """Test detection of frost risk."""
        # Freezing weather
        weather_data = [
            WeatherData(
                time=datetime(2023, 6, 1),
                temperature_2m_mean=5.0,
                temperature_2m_max=8.0,
                temperature_2m_min=-2.0  # Below frost_threshold (0.0)
            )
        ]
        
        violations = checker.check_violations(
            allocation=allocation,
            weather_data=weather_data,
            crop_profile=crop_profile
        )
        
        # Filter frost risk violations
        frost_violations = [
            v for v in violations 
            if v.violation_type == ViolationType.FROST_RISK
        ]
        
        assert len(frost_violations) >= 1, "Frost risk should be detected"
        assert frost_violations[0].severity == "warning"
        assert "Frost risk" in frost_violations[0].message
        assert "-2.0" in frost_violations[0].message
    
    def test_sterility_risk(self, checker, allocation, crop_profile):
        """Test detection of sterility risk."""
        # Very hot weather
        weather_data = [
            WeatherData(
                time=datetime(2023, 6, 1),
                temperature_2m_mean=30.0,
                temperature_2m_max=34.0,  # Above sterility_risk_threshold (33.0)
                temperature_2m_min=26.0
            )
        ]
        
        violations = checker.check_violations(
            allocation=allocation,
            weather_data=weather_data,
            crop_profile=crop_profile
        )
        
        # Filter sterility risk violations
        sterility_violations = [
            v for v in violations 
            if v.violation_type == ViolationType.STERILITY_RISK
        ]
        
        assert len(sterility_violations) >= 1, "Sterility risk should be detected"
        assert sterility_violations[0].severity == "warning"
        assert "Sterility risk" in sterility_violations[0].message
        assert "34.0" in sterility_violations[0].message
    
    def test_multiple_stress_types(self, checker, allocation, crop_profile):
        """Test detection of multiple stress types in different days."""
        weather_data = [
            WeatherData(
                time=datetime(2023, 6, 1),
                temperature_2m_mean=25.0,
                temperature_2m_max=35.0,  # High temp stress
                temperature_2m_min=20.0
            ),
            WeatherData(
                time=datetime(2023, 6, 2),
                temperature_2m_mean=12.0,  # Low temp stress
                temperature_2m_max=18.0,
                temperature_2m_min=8.0
            ),
        ]
        
        violations = checker.check_violations(
            allocation=allocation,
            weather_data=weather_data,
            crop_profile=crop_profile
        )
        
        # Check both stress types are detected
        high_temp = [v for v in violations if v.violation_type == ViolationType.HIGH_TEMP_STRESS]
        low_temp = [v for v in violations if v.violation_type == ViolationType.LOW_TEMP_STRESS]
        
        assert len(high_temp) >= 1, "High temperature stress should be detected"
        assert len(low_temp) >= 1, "Low temperature stress should be detected"
    
    def test_no_crop_profile_no_violations(self, checker, field):
        """Test that crops without crop_profile don't trigger violations."""
        crop_no_profiles = Crop(
            crop_id="bean",
            name="インゲン",
            variety="つるなし",
            area_per_unit=1.0
        )
        # No temperature_profiles attribute
        
        allocation = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop_no_profiles,
            start_date=datetime(2023, 6, 1),
            completion_date=datetime(2023, 7, 31),
            area_used=100.0,
            growth_days=60,
            accumulated_gdd=1200.0,
            total_cost=30000.0
        )
        
        weather_data = [
            WeatherData(
                time=datetime(2023, 6, 1),
                temperature_2m_mean=25.0,
                temperature_2m_max=35.0,
                temperature_2m_min=15.0
            )
        ]
        
        violations = checker.check_violations(
            allocation=allocation,
            weather_data=weather_data,
            crop_profile=None  # No crop profile provided
        )
        
        # No temperature stress violations should be found
        temp_violations = [
            v for v in violations 
            if v.violation_type in [
                ViolationType.HIGH_TEMP_STRESS,
                ViolationType.LOW_TEMP_STRESS,
                ViolationType.FROST_RISK,
                ViolationType.STERILITY_RISK
            ]
        ]
        
        assert len(temp_violations) == 0, "No violations expected for crops without temp profiles"
