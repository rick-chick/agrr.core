"""Tests for optimization result saving in GrowthPeriodOptimizeInteractor."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

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
from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
    GrowthPeriodOptimizeInteractor,
)


@pytest.mark.asyncio
class TestOptimizationResultSaving:
    """Test cases for optimization result saving functionality."""

    async def test_saves_intermediate_results_when_gateway_provided(self):
        """Test that intermediate results are saved when gateway is provided."""
        # Setup mocks
        gateway_crop_requirement = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_optimization_result_gateway = AsyncMock()

        # Setup crop requirements (total 100 GDD)
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
        stage = GrowthStage(name="Growth", order=1)

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
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data: 10 GDD per day
        weather_data = [
            WeatherData(
                time=datetime(2024, 4, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for day in range(1, 21)
        ]

        gateway_crop_requirement.get.return_value = crop_requirement
        mock_weather_gateway.get.return_value = weather_data

        # Create interactor with optimization result gateway
        interactor = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=gateway_crop_requirement,
            weather_gateway=mock_weather_gateway,
            optimization_result_gateway=mock_optimization_result_gateway,
        )

        # Execute optimization
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 15),
            field=test_field,
        )

        response = await interactor.execute(request)

        # Verify that save was called
        mock_optimization_result_gateway.save.assert_called_once()
        
        # Verify the arguments passed to save
        call_args = mock_optimization_result_gateway.save.call_args
        optimization_id = call_args[0][0]
        intermediate_results = call_args[0][1]

        # Check optimization ID format
        assert "rice" in optimization_id
        assert "Koshihikari" in optimization_id

        # Check intermediate results
        assert len(intermediate_results) > 0
        
        # Check that each result has the required fields
        for result in intermediate_results:
            assert result.start_date is not None
            assert result.base_temperature == 10.0
            assert result.accumulated_gdd >= 0.0
            if result.completion_date:
                assert result.completion_date >= result.start_date

    async def test_does_not_save_when_gateway_not_provided(self):
        """Test that no saving occurs when gateway is not provided."""
        # Setup mocks
        gateway_crop_requirement = AsyncMock()
        mock_weather_gateway = AsyncMock()

        # Setup crop requirements (total 100 GDD)
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
        stage = GrowthStage(name="Growth", order=1)

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
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data: 10 GDD per day
        weather_data = [
            WeatherData(
                time=datetime(2024, 4, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for day in range(1, 21)
        ]

        gateway_crop_requirement.get.return_value = crop_requirement
        mock_weather_gateway.get.return_value = weather_data

        # Create interactor without optimization result gateway
        interactor = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=gateway_crop_requirement,
            weather_gateway=mock_weather_gateway,
            optimization_result_gateway=None,
        )

        # Execute optimization
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 15),
            field=test_field,
        )

        # Should not raise any errors
        response = await interactor.execute(request)
        
        # Verify response is still valid
        assert response.optimal_start_date is not None
        assert response.completion_date is not None

    async def test_saved_results_contain_accumulated_gdd(self):
        """Test that saved results contain accurate accumulated GDD."""
        # Setup mocks
        gateway_crop_requirement = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_optimization_result_gateway = AsyncMock()

        # Setup crop requirements (total 100 GDD)
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
        stage = GrowthStage(name="Growth", order=1)

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
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data: 10 GDD per day
        weather_data = [
            WeatherData(
                time=datetime(2024, 4, day),
                temperature_2m_mean=20.0,  # 20 - 10 (base) = 10 GDD/day
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for day in range(1, 21)
        ]

        gateway_crop_requirement.get.return_value = crop_requirement
        mock_weather_gateway.get.return_value = weather_data

        # Create interactor with optimization result gateway
        interactor = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=gateway_crop_requirement,
            weather_gateway=mock_weather_gateway,
            optimization_result_gateway=mock_optimization_result_gateway,
        )

        # Execute optimization
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 15),
            field=test_field,
        )

        response = await interactor.execute(request)

        # Get saved results
        call_args = mock_optimization_result_gateway.save.call_args
        intermediate_results = call_args[0][1]

        # Verify accumulated GDD is at least 100 (required for completion)
        for result in intermediate_results:
            if result.completion_date:
                assert result.accumulated_gdd >= 100.0

