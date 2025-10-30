"""Tests for TaskSchedule entity."""

import pytest

from agrr_core.entity.entities.task_schedule_entity import TaskSchedule

class TestTaskSchedule:
    """Test cases for TaskSchedule entity."""
    
    def test_task_schedule_creation(self):
        """Test TaskSchedule creation."""
        schedule = TaskSchedule(
            task_id="soil_preparation",
            stage_order=1,
            gdd_trigger=0,
            gdd_tolerance=0,
            priority=1,
            precipitation_max=0.5,
            wind_speed_max=10.0,
            description="栽培開始前の土壌準備"
        )
        
        assert schedule.task_id == "soil_preparation"
        assert schedule.stage_order == 1
        assert schedule.gdd_trigger == 0
        assert schedule.gdd_tolerance == 0
        assert schedule.priority == 1
        assert schedule.precipitation_max == 0.5
        assert schedule.wind_speed_max == 10.0
        assert schedule.temperature_min is None
        assert schedule.temperature_max is None
        assert schedule.description == "栽培開始前の土壌準備"
    
    def test_task_schedule_with_temperature(self):
        """Test TaskSchedule with temperature constraints."""
        schedule = TaskSchedule(
            task_id="seeding",
            stage_order=1,
            gdd_trigger=0,
            gdd_tolerance=0,
            priority=2,
            precipitation_max=0.1,
            wind_speed_max=5.0,
            temperature_min=15.0,
            temperature_max=25.0,
            description="栽培開始時の播種作業"
        )
        
        assert schedule.temperature_min == 15.0
        assert schedule.temperature_max == 25.0
    
    def test_is_startup_task(self):
        """Test startup task check."""
        # Startup task (gdd_tolerance = 0)
        startup_schedule = TaskSchedule(
            task_id="soil_preparation",
            stage_order=1,
            gdd_trigger=0,
            gdd_tolerance=0,
            priority=1,
            precipitation_max=0.5,
            wind_speed_max=10.0
        )
        assert startup_schedule.is_startup_task() is True
        assert startup_schedule.is_ongoing_task() is False
        
        # Ongoing task (gdd_tolerance > 0)
        ongoing_schedule = TaskSchedule(
            task_id="fertilization",
            stage_order=2,
            gdd_trigger=200,
            gdd_tolerance=50,
            priority=3,
            precipitation_max=1.0,
            wind_speed_max=8.0
        )
        assert ongoing_schedule.is_startup_task() is False
        assert ongoing_schedule.is_ongoing_task() is True
    
    def test_get_execution_window(self):
        """Test execution window calculation."""
        schedule = TaskSchedule(
            task_id="fertilization",
            stage_order=2,
            gdd_trigger=200,
            gdd_tolerance=50,
            priority=3,
            precipitation_max=1.0,
            wind_speed_max=8.0
        )
        
        min_gdd, max_gdd = schedule.get_execution_window()
        assert min_gdd == 150  # 200 - 50
        assert max_gdd == 250  # 200 + 50
    
    def test_can_execute_at_gdd(self):
        """Test GDD execution check."""
        schedule = TaskSchedule(
            task_id="fertilization",
            stage_order=2,
            gdd_trigger=200,
            gdd_tolerance=50,
            priority=3,
            precipitation_max=1.0,
            wind_speed_max=8.0
        )
        
        # Within execution window
        assert schedule.can_execute_at_gdd(200) is True
        assert schedule.can_execute_at_gdd(150) is True
        assert schedule.can_execute_at_gdd(250) is True
        
        # Outside execution window
        assert schedule.can_execute_at_gdd(100) is False
        assert schedule.can_execute_at_gdd(300) is False
    
    def test_startup_task_execution_window(self):
        """Test execution window for startup tasks."""
        schedule = TaskSchedule(
            task_id="soil_preparation",
            stage_order=1,
            gdd_trigger=0,
            gdd_tolerance=0,
            priority=1,
            precipitation_max=0.5,
            wind_speed_max=10.0
        )
        
        min_gdd, max_gdd = schedule.get_execution_window()
        assert min_gdd == 0  # 0 - 0
        assert max_gdd == 0  # 0 + 0
        
        # Startup tasks can only execute at exactly gdd_trigger
        assert schedule.can_execute_at_gdd(0) is True
        assert schedule.can_execute_at_gdd(1) is False
        assert schedule.can_execute_at_gdd(-1) is False
