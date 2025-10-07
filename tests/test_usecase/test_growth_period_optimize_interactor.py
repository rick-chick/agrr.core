"""Tests for GrowthPeriodOptimizeInteractor."""

import pytest
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
from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
    GrowthPeriodOptimizeInteractor,
)


class TestGrowthPeriodOptimizeInteractor:
    """Test cases for GrowthPeriodOptimizeInteractor."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_growth_progress_crop_requirement_gateway,
        mock_growth_progress_weather_gateway,
    ):
        """Set up test fixtures using conftest mocks."""
        self.mock_crop_requirement_gateway = mock_growth_progress_crop_requirement_gateway
        self.mock_weather_gateway = mock_growth_progress_weather_gateway
        self.interactor = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=self.mock_crop_requirement_gateway,
            weather_gateway=self.mock_weather_gateway,
        )

    @pytest.mark.asyncio
    async def test_execute_finds_optimal_period(self):
        """Test that the interactor finds the optimal growth period with minimum cost."""
        # Setup mock crop requirements (total 100 GDD)
        crop = Crop(crop_id="rice", name="Rice", variety="Koshihikari")
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

        # Weather data: Same weather but different completion dates based on start date
        # All days have 10 GDD/day (temp=20, base=10 -> GDD=10)
        # Need 100 GDD total -> 10 days to complete from any start date
        weather_data = [
            WeatherData(time=datetime(2024, 4, 1), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 2), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 3), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 4), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 5), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 6), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 7), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 8), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 9), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 10), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 11), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 12), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 13), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 14), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 15), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 16), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 17), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 18), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 19), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 20), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
        ]

        self.mock_crop_requirement_gateway.craft.return_value = crop_requirement
        self.mock_weather_gateway.get.return_value = weather_data

        # Request with 2 candidate dates and daily cost of 1000
        # Both candidates will take 10 days (same weather) so same cost
        # First candidate should be optimal (earliest start date with minimum cost)
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            candidate_start_dates=[datetime(2024, 4, 1), datetime(2024, 4, 5)],
            weather_data_file="weather_data.json",
            daily_fixed_cost=1000.0,
        )

        response = await self.interactor.execute(request)

        # Assertions
        assert response.crop_name == "Rice"
        assert response.variety == "Koshihikari"
        assert response.daily_fixed_cost == 1000.0
        
        # April 5 is optimal (6 days * 1000 = 6000) vs April 1 (10 days * 1000 = 10000)
        # Both reach 100% on April 10, but April 5 starts later so fewer days
        assert response.optimal_start_date == datetime(2024, 4, 5)
        assert response.completion_date == datetime(2024, 4, 10)
        assert response.growth_days == 6
        assert response.total_cost == 6000.0

        # Check candidates
        assert len(response.candidates) == 2
        
        # First candidate (April 1): 10 days
        candidate1 = response.candidates[0]
        assert candidate1.start_date == datetime(2024, 4, 1)
        assert candidate1.completion_date == datetime(2024, 4, 10)
        assert candidate1.growth_days == 10
        assert candidate1.total_cost == 10000.0
        assert candidate1.is_optimal is False

        # Second candidate (April 5): 6 days (optimal - lower cost)
        candidate2 = response.candidates[1]
        assert candidate2.start_date == datetime(2024, 4, 5)
        assert candidate2.completion_date == datetime(2024, 4, 10)
        assert candidate2.growth_days == 6
        assert candidate2.total_cost == 6000.0
        assert candidate2.is_optimal is True

    @pytest.mark.asyncio
    async def test_execute_handles_incomplete_growth(self):
        """Test handling when growth doesn't reach 100% for some candidates."""
        # Setup mock crop requirements (total 1000 GDD - high requirement)
        crop = Crop(crop_id="rice", name="Rice")
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
            thermal=ThermalRequirement(required_gdd=1000.0),
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req]
        )

        # Limited weather data: only 5 days with 10 GDD/day = 50 GDD total (< 1000)
        weather_data = [
            WeatherData(time=datetime(2024, 4, 1), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 2), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 3), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 4), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 5), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
        ]

        self.mock_crop_requirement_gateway.craft.return_value = crop_requirement
        self.mock_weather_gateway.get.return_value = weather_data

        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety=None,
            candidate_start_dates=[datetime(2024, 4, 1)],
            weather_data_file="weather_data.json",
            daily_fixed_cost=1000.0,
        )

        # Should raise exception when no candidate completes
        with pytest.raises(ValueError, match="No candidate reached 100% growth"):
            await self.interactor.execute(request)

    @pytest.mark.asyncio
    async def test_execute_with_single_candidate(self):
        """Test with a single candidate date."""
        # Setup simple scenario
        crop = Crop(crop_id="tomato", name="Tomato")
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
            thermal=ThermalRequirement(required_gdd=50.0),
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req]
        )

        weather_data = [
            WeatherData(time=datetime(2024, 5, 1), temperature_2m_mean=25.0, temperature_2m_max=30.0, temperature_2m_min=20.0),
            WeatherData(time=datetime(2024, 5, 2), temperature_2m_mean=25.0, temperature_2m_max=30.0, temperature_2m_min=20.0),
            WeatherData(time=datetime(2024, 5, 3), temperature_2m_mean=25.0, temperature_2m_max=30.0, temperature_2m_min=20.0),
            WeatherData(time=datetime(2024, 5, 4), temperature_2m_mean=25.0, temperature_2m_max=30.0, temperature_2m_min=20.0),
        ]

        self.mock_crop_requirement_gateway.craft.return_value = crop_requirement
        self.mock_weather_gateway.get.return_value = weather_data

        request = OptimalGrowthPeriodRequestDTO(
            crop_id="tomato",
            variety=None,
            candidate_start_dates=[datetime(2024, 5, 1)],
            weather_data_file="weather_data.json",
            daily_fixed_cost=500.0,
        )

        response = await self.interactor.execute(request)

        # Single candidate is automatically optimal
        assert response.optimal_start_date == datetime(2024, 5, 1)
        assert response.growth_days == 4  # 15 GDD/day * 4 = 60 GDD (> 50)
        assert response.total_cost == 2000.0  # 4 days * 500
        assert len(response.candidates) == 1
        assert response.candidates[0].is_optimal is True

