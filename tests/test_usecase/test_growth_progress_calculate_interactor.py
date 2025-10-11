"""Tests for GrowthProgressCalculateInteractor."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.usecase.dto.growth_progress_calculate_request_dto import (
    GrowthProgressCalculateRequestDTO,
)
from agrr_core.usecase.interactors.growth_progress_calculate_interactor import (
    GrowthProgressCalculateInteractor,
)


class TestGrowthProgressCalculateInteractor:
    """Test cases for GrowthProgressCalculateInteractor."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_growth_progress_crop_requirement_gateway,
        mock_growth_progress_weather_gateway,
    ):
        """Set up test fixtures using conftest mocks."""
        self.mock_crop_requirement_gateway = mock_growth_progress_crop_requirement_gateway
        self.mock_weather_gateway = mock_growth_progress_weather_gateway
        self.interactor = GrowthProgressCalculateInteractor(
            crop_requirement_gateway=self.mock_crop_requirement_gateway,
            weather_gateway=self.mock_weather_gateway,
        )

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful growth progress calculation."""
        # Setup mock crop requirements
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
        stage1 = GrowthStage(name="Vegetative", order=1)
        stage2 = GrowthStage(name="Maturity", order=2)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
        )
        sunshine_profile = SunshineProfile(
            minimum_sunshine_hours=4.0, target_sunshine_hours=8.0
        )

        stage_req1 = StageRequirement(
            stage=stage1,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=500.0),
        )
        stage_req2 = StageRequirement(
            stage=stage2,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=500.0),
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req1, stage_req2]
        )

        # Setup mock weather data
        weather_data = [
            WeatherData(
                time=datetime(2024, 5, 1),
                temperature_2m_mean=25.0,  # GDD = 25 - 10 = 15
                temperature_2m_max=30.0,
                temperature_2m_min=20.0,
            ),
            WeatherData(
                time=datetime(2024, 5, 2),
                temperature_2m_mean=25.0,  # GDD = 25 - 10 = 15
                temperature_2m_max=30.0,
                temperature_2m_min=20.0,
            ),
        ]

        weather_dto = WeatherDataWithLocationDTO(
            weather_data_list=weather_data, location=None
        )

        self.mock_crop_requirement_gateway.craft.return_value = crop_requirement
        self.mock_weather_gateway.get.return_value = weather_data

        # Execute
        request = GrowthProgressCalculateRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            start_date=datetime(2024, 5, 1),
            weather_data_file="weather_data.json",
        )

        response = await self.interactor.execute(request)

        # Assertions
        assert response.crop_name == "Rice"
        assert response.variety == "Koshihikari"
        assert response.start_date == datetime(2024, 5, 1)
        assert len(response.progress_records) == 2

        # Check first day
        record1 = response.progress_records[0]
        assert record1.date == datetime(2024, 5, 1)
        assert record1.cumulative_gdd == 15.0
        assert record1.total_required_gdd == 1000.0
        assert record1.growth_percentage == 1.5
        assert record1.stage_name == "Vegetative"
        assert record1.is_complete is False

        # Check second day
        record2 = response.progress_records[1]
        assert record2.date == datetime(2024, 5, 2)
        assert record2.cumulative_gdd == 30.0
        assert record2.growth_percentage == 3.0
        assert record2.is_complete is False

    @pytest.mark.asyncio
    async def test_execute_completes_at_100_percent(self):
        """Test that growth caps at 100%."""
        # Setup mock crop requirements with small GDD requirement
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
        stage = GrowthStage(name="Test", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=10.0),  # Small requirement
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data that will exceed GDD requirement
        weather_data = [
            WeatherData(
                time=datetime(2024, 5, 1),
                temperature_2m_mean=30.0,  # GDD = 30 - 10 = 20 (exceeds 10)
                temperature_2m_max=35.0,
                temperature_2m_min=25.0,
            ),
        ]

        weather_dto = WeatherDataWithLocationDTO(
            weather_data_list=weather_data, location=None
        )

        self.mock_crop_requirement_gateway.craft.return_value = crop_requirement
        self.mock_weather_gateway.get.return_value = weather_data

        # Execute
        request = GrowthProgressCalculateRequestDTO(
            crop_id="rice",
            variety=None,
            start_date=datetime(2024, 5, 1),
            weather_data_file="weather_data.json",
        )

        response = await self.interactor.execute(request)

        # Assertions
        assert len(response.progress_records) == 1
        record = response.progress_records[0]
        assert record.growth_percentage == 100.0  # Capped at 100
        assert record.is_complete is True

    @pytest.mark.asyncio
    async def test_determine_current_stage(self):
        """Test stage determination based on cumulative GDD."""
        # Create stages with different GDD requirements
        stage1 = GrowthStage(name="Stage1", order=1)
        stage2 = GrowthStage(name="Stage2", order=2)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req1 = StageRequirement(
            stage=stage1,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )
        stage_req2 = StageRequirement(
            stage=stage2,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        stage_requirements = [stage_req1, stage_req2]

        # Test stage 1 (GDD < 100)
        current_stage = self.interactor._determine_current_stage(50.0, stage_requirements)
        assert current_stage.stage.name == "Stage1"

        # Test stage 2 (100 <= GDD < 200)
        current_stage = self.interactor._determine_current_stage(150.0, stage_requirements)
        assert current_stage.stage.name == "Stage2"

        # Test beyond all stages (GDD >= 200)
        current_stage = self.interactor._determine_current_stage(250.0, stage_requirements)
        assert current_stage.stage.name == "Stage2"  # Returns last stage

