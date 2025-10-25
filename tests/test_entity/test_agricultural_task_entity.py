"""Tests for AgriculturalTask entity."""

import pytest

from agrr_core.entity.entities.agricultural_task_entity import AgriculturalTask


class TestAgriculturalTask:
    """Test cases for AgriculturalTask entity."""
    
    def test_agricultural_task_creation(self):
        """Test AgriculturalTask creation."""
        task = AgriculturalTask(
            task_id="soil_preparation",
            task_name="土壌準備",
            description="畑の耕起、施肥、マルチング",
            time_per_sqm=0.5,
            weather_dependency="low",
            precipitation_max=0.5,
            wind_speed_max=10.0
        )
        
        assert task.task_id == "soil_preparation"
        assert task.task_name == "土壌準備"
        assert task.description == "畑の耕起、施肥、マルチング"
        assert task.time_per_sqm == 0.5
        assert task.weather_dependency == "low"
        assert task.precipitation_max == 0.5
        assert task.wind_speed_max == 10.0
        assert task.temperature_min is None
        assert task.temperature_max is None
    
    def test_agricultural_task_with_temperature(self):
        """Test AgriculturalTask with temperature constraints."""
        task = AgriculturalTask(
            task_id="seeding",
            task_name="播種",
            description="種子の播種作業",
            time_per_sqm=0.1,
            weather_dependency="low",
            precipitation_max=0.1,
            wind_speed_max=5.0,
            temperature_min=15.0,
            temperature_max=25.0
        )
        
        assert task.temperature_min == 15.0
        assert task.temperature_max == 25.0
    
    def test_is_weather_dependent(self):
        """Test weather dependency check."""
        # High dependency
        high_task = AgriculturalTask(
            task_id="pest_control",
            task_name="病害虫防除",
            description="農薬散布",
            time_per_sqm=0.2,
            weather_dependency="high",
            precipitation_max=0.0,
            wind_speed_max=3.0
        )
        assert high_task.is_weather_dependent() is True
        
        # Medium dependency
        medium_task = AgriculturalTask(
            task_id="harvesting",
            task_name="収穫",
            description="収穫作業",
            time_per_sqm=0.4,
            weather_dependency="medium",
            precipitation_max=0.5,
            wind_speed_max=8.0
        )
        assert medium_task.is_weather_dependent() is True
        
        # Low dependency
        low_task = AgriculturalTask(
            task_id="soil_preparation",
            task_name="土壌準備",
            description="土壌準備",
            time_per_sqm=0.5,
            weather_dependency="low",
            precipitation_max=0.5,
            wind_speed_max=10.0
        )
        assert low_task.is_weather_dependent() is False
    
    def test_can_execute_in_weather(self):
        """Test weather condition execution check."""
        task = AgriculturalTask(
            task_id="seeding",
            task_name="播種",
            description="種子の播種作業",
            time_per_sqm=0.1,
            weather_dependency="low",
            precipitation_max=0.1,
            wind_speed_max=5.0,
            temperature_min=15.0,
            temperature_max=25.0
        )
        
        # Good conditions
        assert task.can_execute_in_weather(0.0, 3.0, 20.0) is True
        
        # Too much precipitation
        assert task.can_execute_in_weather(0.2, 3.0, 20.0) is False
        
        # Too much wind
        assert task.can_execute_in_weather(0.0, 6.0, 20.0) is False
        
        # Too cold
        assert task.can_execute_in_weather(0.0, 3.0, 10.0) is False
        
        # Too hot
        assert task.can_execute_in_weather(0.0, 3.0, 30.0) is False
        
        # Without temperature (should work)
        assert task.can_execute_in_weather(0.0, 3.0) is True
    
    def test_can_execute_in_weather_without_temperature(self):
        """Test weather condition execution check without temperature."""
        task = AgriculturalTask(
            task_id="soil_preparation",
            task_name="土壌準備",
            description="土壌準備",
            time_per_sqm=0.5,
            weather_dependency="low",
            precipitation_max=0.5,
            wind_speed_max=10.0
        )
        
        # Good conditions
        assert task.can_execute_in_weather(0.3, 8.0) is True
        
        # Too much precipitation
        assert task.can_execute_in_weather(0.6, 8.0) is False
        
        # Too much wind
        assert task.can_execute_in_weather(0.3, 12.0) is False
