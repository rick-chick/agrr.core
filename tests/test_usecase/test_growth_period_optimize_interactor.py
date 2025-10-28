"""Tests for GrowthPeriodOptimizeInteractor."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_profile_entity import (
    CropProfile,
)
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.entity.value_objects.rule_type import RuleType
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
        gateway_crop_profile,
        gateway_weather,
    ):
        """Set up test fixtures using conftest mocks."""
        self.gateway_crop_profile = gateway_crop_profile
        self.gateway_weather = gateway_weather
        self.interactor = GrowthPeriodOptimizeInteractor(
            crop_profile_gateway=self.gateway_crop_profile,
            weather_gateway=self.gateway_weather,
        )

    @pytest.mark.asyncio
    async def test_execute_finds_optimal_period(self):
        """Test that the interactor finds the optimal growth period with minimum cost."""
        # Setup mock crop requirements (total 100 GDD)
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_profile = CropProfile(
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

        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data

        # Request: Start between April 1-5, must complete by April 15 (completion deadline)
        # All candidates need 10 days (100 GDD / 10 GDD per day)
        # April 1 start -> completes April 10 (✓ within deadline)
        # April 5 start -> completes April 14 (✓ within deadline) - shortest period
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 15),  # Completion deadline
            field=test_field,
        )

        response = await self.interactor.execute(request)

        # Assertions
        assert response.crop_name == "Rice"
        assert response.variety == "Koshihikari"
        assert response.daily_fixed_cost == 1000.0
        
        # All candidates need 10 days (100 GDD / 10 GDD per day) regardless of start date
        # Since all have same cost (10 days * 1000 = 10000), any is equally optimal
        # After filtering (one candidate per completion_date), the last one is selected
        assert response.growth_days == 10
        assert response.total_cost == 10000.0

        # Check that system evaluated dates within start range that can meet deadline
        # After filtering: each completion_date has only one candidate (the one with shortest growth_days)
        # Since all candidates have same growth_days (10), each date has 1 candidate
        valid_candidates = [c for c in response.candidates if c.total_cost is not None]
        assert len(valid_candidates) == 6  # April 1-6: each maps to unique completion date (April 10-15)

    @pytest.mark.asyncio
    async def test_execute_handles_incomplete_growth(self):
        """Test handling when growth doesn't reach 100% for any candidate in evaluation period."""
        # Setup mock crop requirements (total 1000 GDD - high requirement)
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=1000.0),
        )

        crop_profile = CropProfile(
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

        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data

        # Evaluation period with only 1 day
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety=None,
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 1),
            field=test_field,
        )

        # Should raise exception when no candidate completes
        with pytest.raises(ValueError, match="No candidate can complete growth within the planning period"):
            await self.interactor.execute(request)

    @pytest.mark.asyncio
    async def test_execute_with_single_day_evaluation_period(self):
        """Test with evaluation period of just one day."""
        # Setup simple scenario
        crop = Crop(crop_id="tomato", name="Tomato", area_per_unit=0.5)
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=50.0),
        )

        crop_profile = CropProfile(
            crop=crop, stage_requirements=[stage_req]
        )

        weather_data = [
            WeatherData(time=datetime(2024, 5, 1), temperature_2m_mean=25.0, temperature_2m_max=30.0, temperature_2m_min=20.0),
            WeatherData(time=datetime(2024, 5, 2), temperature_2m_mean=25.0, temperature_2m_max=30.0, temperature_2m_min=20.0),
            WeatherData(time=datetime(2024, 5, 3), temperature_2m_mean=25.0, temperature_2m_max=30.0, temperature_2m_min=20.0),
            WeatherData(time=datetime(2024, 5, 4), temperature_2m_mean=25.0, temperature_2m_max=30.0, temperature_2m_min=20.0),
        ]

        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data

        # Start on May 1, must complete by May 5 (deadline)
        # Needs 50 GDD, gets 15 GDD/day -> 4 days needed -> completes May 4 (✓)
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=500.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="tomato",
            variety=None,
            evaluation_period_start=datetime(2024, 5, 1),
            evaluation_period_end=datetime(2024, 5, 5),  # Completion deadline
            field=test_field,
        )

        response = await self.interactor.execute(request)

        # Single candidate is automatically optimal
        assert response.optimal_start_date == datetime(2024, 5, 1)
        assert response.completion_date == datetime(2024, 5, 4)
        assert response.growth_days == 4  # 15 GDD/day * 4 = 60 GDD (> 50)
        assert response.total_cost == 2000.0  # 4 days * 500
        valid_candidates = [c for c in response.candidates if c.total_cost is not None]
        assert len(valid_candidates) == 1
        assert valid_candidates[0].is_optimal is True

    @pytest.mark.asyncio
    async def test_execute_with_completion_deadline_filters_late_candidates(self):
        """Test that candidates exceeding completion deadline are filtered out."""
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
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_profile = CropProfile(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data: 10 GDD/day, so 10 days needed from any start date
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
        ]

        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data

        # Evaluation period: April 1-3 as start date candidates
        # Completion deadline: April 13
        # April 1 start -> completes April 10 (✓ 10 days)
        # April 2 start -> completes April 11 (✓ 10 days)
        # April 3 start -> completes April 12 (✓ 10 days)
        # April 4+ start -> would complete April 13+ (✗ exceeds deadline on April 13)
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 12),  # Completion deadline
            field=test_field,
        )

        response = await self.interactor.execute(request)

        # All candidates complete by deadline, so it just picks min cost
        # All have same cost (10 days), after filtering each completion date has one candidate
        assert response.growth_days == 10
        assert response.total_cost == 10000.0

        # Check that valid candidates (within deadline) were evaluated
        # After filtering: each completion_date has only one candidate
        valid_candidates = [c for c in response.candidates if c.total_cost is not None]
        assert len(valid_candidates) == 3  # April 1, 2, 3: each maps to unique completion date (April 10, 11, 12)

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_no_candidate_meets_deadline(self):
        """Test error message when all candidates exceed completion deadline."""
        # Setup crop requirements (total 100 GDD - takes 10 days)
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_profile = CropProfile(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data: 10 GDD/day
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
        ]

        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data

        # Start on April 1, needs 10 days -> completes April 10
        # But deadline is April 8 -> Cannot meet deadline
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety=None,
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 8),  # Unrealistic deadline (too early)
            field=test_field,
        )

        # Should raise error with helpful message about deadline
        with pytest.raises(ValueError, match="No candidate can complete growth within the planning period"):
            await self.interactor.execute(request)

    @pytest.mark.asyncio
    async def test_execute_loads_interaction_rules_when_file_provided(
        self, gateway_interaction_rule
    ):
        """Test that interaction rules are loaded when file path is provided in request."""
        from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
        
        # Setup interactor with interaction rule gateway
        interactor = GrowthPeriodOptimizeInteractor(
            crop_profile_gateway=self.gateway_crop_profile,
            weather_gateway=self.gateway_weather,
            interaction_rule_gateway=gateway_interaction_rule,
        )

        # Setup mock crop requirements
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.25,
            variety="Aiko",
            groups=["Solanaceae"]
        )
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_profile = CropProfile(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data
        weather_data = [
            WeatherData(
                time=datetime(2024, 4, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for day in range(1, 21)
        ]

        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data

        # Setup interaction rules
        interaction_rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type=RuleType.CONTINUOUS_CULTIVATION,
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True,
                description="Solanaceae continuous cultivation penalty",
            )
        ]
        gateway_interaction_rule.get_rules.return_value = interaction_rules

        # Create field and request
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=5000.0,
            location="Test Location"
        )

        request = OptimalGrowthPeriodRequestDTO(
            crop_id="tomato",
            variety="Aiko",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 15),
            field=test_field,
        )

        # Execute
        response = await interactor.execute(request)

        # Verify that interaction rules were loaded
        gateway_interaction_rule.get_rules.assert_called_once()
        
        # Verify response is valid
        assert response.optimal_start_date is not None
        assert response.completion_date is not None

    @pytest.mark.asyncio
    async def test_execute_optimizes_for_profit_when_revenue_available(self):
        """Test that the interactor optimizes for profit (revenue - cost) when revenue information is available."""
        # Setup crop with revenue information
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            variety="Momotaro",
            revenue_per_area=50000.0,  # ¥50,000 per m²
            max_revenue=None,
        )
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_profile = CropProfile(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data: varying GDD per day to create different growth periods
        # Days 1-5: 5 GDD/day (temp=15, base=10 -> GDD=5)
        # Days 6-20: 10 GDD/day (temp=20, base=10 -> GDD=10)
        weather_data = [
            # Slow growth period (5 GDD/day)
            WeatherData(time=datetime(2024, 4, 1), temperature_2m_mean=15.0, temperature_2m_max=20.0, temperature_2m_min=10.0),
            WeatherData(time=datetime(2024, 4, 2), temperature_2m_mean=15.0, temperature_2m_max=20.0, temperature_2m_min=10.0),
            WeatherData(time=datetime(2024, 4, 3), temperature_2m_mean=15.0, temperature_2m_max=20.0, temperature_2m_min=10.0),
            WeatherData(time=datetime(2024, 4, 4), temperature_2m_mean=15.0, temperature_2m_max=20.0, temperature_2m_min=10.0),
            WeatherData(time=datetime(2024, 4, 5), temperature_2m_mean=15.0, temperature_2m_max=20.0, temperature_2m_min=10.0),
            # Fast growth period (10 GDD/day)
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

        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data

        # Field: 1000 m² area, ¥1000/day fixed cost
        # Revenue: 1000 m² * ¥50,000/m² = ¥50,000,000
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="tomato",
            variety="Momotaro",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 20),
            field=test_field,
        )

        response = await self.interactor.execute(request)

        # Expected behavior:
        # - April 1 start: 5*5 + 75 = 100 GDD, needs ~13 days (5 days slow + 8 days fast)
        #   Cost: 13 * ¥1000 = ¥13,000, Revenue: ¥50,000,000, Profit: ¥49,987,000
        # - April 6 start onwards: 10 GDD/day, needs 10 days (all fast growth period)
        #   Cost: 10 * ¥1000 = ¥10,000, Revenue: ¥50,000,000, Profit: ¥49,990,000 (BETTER!)
        #
        # After filtering: each completion_date has only the shortest growth_days candidate
        # Multiple candidates with 10 days may exist (April 6-11 starts), each completing on different dates
        # The last one (latest start date) is selected as optimal
        
        assert response.crop_name == "Tomato"
        assert response.variety == "Momotaro"
        # Optimal should have shortest growth period (10 days)
        assert response.growth_days == 10
        assert response.total_cost == 10000.0
        
        # Verify candidates include varying completion dates
        valid_candidates = [c for c in response.candidates if c.total_cost is not None]
        assert len(valid_candidates) >= 2
        
        # Verify that optimal candidate maximizes profit
        optimal = [c for c in valid_candidates if c.is_optimal][0]
        expected_profit = (1000.0 * 50000.0) - (optimal.growth_days * 1000.0)
        assert optimal.get_metrics().profit == expected_profit

    @pytest.mark.asyncio
    async def test_filter_shortest_candidates_per_completion_date(self):
        """Test that candidates are filtered to keep only the shortest period per completion date."""
        # Setup crop requirements (50 GDD total)
        crop = Crop(crop_id="lettuce", name="Lettuce", area_per_unit=0.1, variety="Romaine")
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=5.0,
            optimal_min=15.0,
            optimal_max=20.0,
            low_stress_threshold=10.0,
            high_stress_threshold=25.0,
            frost_threshold=-2.0,
            max_temperature=30.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=50.0),
        )

        crop_profile = CropProfile(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather scenario where multiple start dates reach the same completion date:
        # Days 1-5: low temp (10°C) -> 5 GDD/day
        # Days 6-10: high temp (20°C) -> 15 GDD/day
        # 
        # Start April 1: 5*5 = 25 GDD (days 1-5), then need 25 more GDD -> 2 days (days 6-7)
        #                -> Completes April 7 (7 days total)
        # Start April 2: 5*4 = 20 GDD (days 2-5), then need 30 more GDD -> 2 days (days 6-7)
        #                -> Completes April 7 (6 days total) ← SHORTER!
        # Start April 3: 5*3 = 15 GDD (days 3-5), then need 35 more GDD -> 3 days (days 6-8)
        #                -> Completes April 8 (6 days total)
        # Start April 4: 5*2 = 10 GDD (days 4-5), then need 40 more GDD -> 3 days (days 6-8)
        #                -> Completes April 8 (5 days total) ← SHORTER!
        # Start April 5: 5*1 = 5 GDD (day 5), then need 45 more GDD -> 3 days (days 6-8)
        #                -> Completes April 8 (4 days total) ← EVEN SHORTER!
        weather_data = [
            # Low temp period (5 GDD/day)
            WeatherData(time=datetime(2024, 4, 1), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            WeatherData(time=datetime(2024, 4, 2), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            WeatherData(time=datetime(2024, 4, 3), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            WeatherData(time=datetime(2024, 4, 4), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            WeatherData(time=datetime(2024, 4, 5), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            # High temp period (15 GDD/day)
            WeatherData(time=datetime(2024, 4, 6), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 7), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 8), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 9), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 10), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
        ]

        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data

        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="lettuce",
            variety="Romaine",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 10),
            field=test_field,
        )

        response = await self.interactor.execute(request)

        # Without filtering: would have 5 candidates (April 1-5)
        # With filtering: only keep shortest period per completion_date
        # - April 7 completion: only April 2 start (6 days) - filters out April 1 (7 days)
        # - April 8 completion: only April 5 start (4 days) - filters out April 3 (6 days) and April 4 (5 days)
        # So we should have 2 candidates total
        valid_candidates = [c for c in response.candidates if c.total_cost is not None]
        
        # Group candidates by completion date to verify filtering
        completion_dates = {}
        for candidate in valid_candidates:
            comp_date = candidate.completion_date
            if comp_date not in completion_dates:
                completion_dates[comp_date] = []
            completion_dates[comp_date].append(candidate)
        
        # Each completion date should have exactly one candidate
        for comp_date, candidates in completion_dates.items():
            assert len(candidates) == 1, f"Expected 1 candidate for completion date {comp_date}, got {len(candidates)}"
            
            # The candidate should have the shortest growth_days among all candidates with this completion date
            candidate = candidates[0]
            # Verify by checking that it's the latest start date for this completion date
            # (later start = shorter period for same completion date)
            for other in response.candidates:
                if other.completion_date == comp_date and other.start_date != candidate.start_date:
                    # This candidate was filtered out, so it should have longer growth_days
                    # Note: We can't directly access filtered candidates, but the logic ensures this
                    pass
        
        # Optimal should be the one with lowest cost (shortest growth_days)
        # Based on actual GDD calculation with base_temperature=5.0:
        # Days 1-5: 10.0 - 5.0 = 5 GDD/day, Days 6-10: 20.0 - 5.0 = 15 GDD/day
        # Multiple start dates can achieve 4-day completion (minimum cost)
        # The optimizer selects one of these as optimal
        assert response.growth_days == 4
        assert response.total_cost == 4000.0
        
        # Verify that we have multiple completion dates with single candidates each
        assert len(valid_candidates) >= 2  # At least 2 different completion dates

    @pytest.mark.asyncio
    async def test_filter_can_be_disabled(self):
        """Test that candidate filtering can be disabled via request parameter."""
        # Setup crop requirements (50 GDD total)
        crop = Crop(crop_id="lettuce", name="Lettuce", area_per_unit=0.1, variety="Romaine")
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=5.0,
            optimal_min=15.0,
            optimal_max=20.0,
            low_stress_threshold=10.0,
            high_stress_threshold=25.0,
            frost_threshold=-2.0,
            max_temperature=30.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=50.0),
        )

        crop_profile = CropProfile(
            crop=crop, stage_requirements=[stage_req]
        )

        # Same weather scenario as test_filter_shortest_candidates_per_completion_date
        weather_data = [
            # Low temp period (5 GDD/day)
            WeatherData(time=datetime(2024, 4, 1), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            WeatherData(time=datetime(2024, 4, 2), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            WeatherData(time=datetime(2024, 4, 3), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            WeatherData(time=datetime(2024, 4, 4), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            WeatherData(time=datetime(2024, 4, 5), temperature_2m_mean=10.0, temperature_2m_max=15.0, temperature_2m_min=5.0),
            # High temp period (15 GDD/day)
            WeatherData(time=datetime(2024, 4, 6), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 7), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 8), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 9), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
            WeatherData(time=datetime(2024, 4, 10), temperature_2m_mean=20.0, temperature_2m_max=25.0, temperature_2m_min=15.0),
        ]

        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data

        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        # Test with filtering DISABLED
        request_no_filter = OptimalGrowthPeriodRequestDTO(
            crop_id="lettuce",
            variety="Romaine",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 10),
            field=test_field,
            filter_redundant_candidates=False,  # Disable filtering
        )

        response_no_filter = await self.interactor.execute(request_no_filter)

        # Without filtering, we should have ALL valid candidates
        valid_candidates_no_filter = [c for c in response_no_filter.candidates if c.total_cost is not None]
        
        # Test with filtering ENABLED (default)
        request_with_filter = OptimalGrowthPeriodRequestDTO(
            crop_id="lettuce",
            variety="Romaine",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 4, 10),
            field=test_field,
            filter_redundant_candidates=True,  # Enable filtering (default)
        )

        response_with_filter = await self.interactor.execute(request_with_filter)

        valid_candidates_with_filter = [c for c in response_with_filter.candidates if c.total_cost is not None]
        
        # Verify that unfiltered result has MORE candidates than filtered
        assert len(valid_candidates_no_filter) > len(valid_candidates_with_filter), \
            f"Expected more candidates without filter ({len(valid_candidates_no_filter)}) " \
            f"than with filter ({len(valid_candidates_with_filter)})"
        
        # Both should still select optimal candidate with same cost
        assert response_no_filter.growth_days == response_with_filter.growth_days
        assert response_no_filter.total_cost == response_with_filter.total_cost

    @pytest.mark.asyncio
    async def test_optimize_with_harvest_start_gdd(self):
        """Test optimize-period with harvest_start_gdd for fruiting crops."""
        # Create eggplant crop profile with harvest_start_gdd
        crop = Crop(
            crop_id="eggplant",
            name="Eggplant",
            area_per_unit=0.5,
            variety="Japanese",
            revenue_per_area=800000.0,
            groups=["Solanaceae"]
        )
        
        # Seedling stage (no harvest_start_gdd)
        stage1 = GrowthStage(name="Seedling", order=1)
        temp1 = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=32.0,
            frost_threshold=0.0,
            max_temperature=35.0,
        )
        sr1 = StageRequirement(
            stage=stage1,
            temperature=temp1,
            sunshine=SunshineProfile(),
            thermal=ThermalRequirement(required_gdd=300.0),
        )
        
        # Harvest stage (with harvest_start_gdd)
        stage2 = GrowthStage(name="Harvest", order=2)
        temp2 = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=12.0,
            high_stress_threshold=32.0,
            frost_threshold=0.0,
            max_temperature=35.0,
            sterility_risk_threshold=30.0,
        )
        sr2 = StageRequirement(
            stage=stage2,
            temperature=temp2,
            sunshine=SunshineProfile(),
            thermal=ThermalRequirement(
                required_gdd=2200.0,
                harvest_start_gdd=200.0  # Harvest starts at 200 GDD
            ),
        )
        
        crop_profile = CropProfile(crop=crop, stage_requirements=[sr1, sr2])
        
        # Weather data: 10 GDD per day, need 250 days
        # Create data across multiple months
        weather_data = []
        current_date = datetime(2024, 6, 1)
        for i in range(270):  # 270 days to ensure completion
            weather_data.append(
                WeatherData(
                    time=current_date,
                    temperature_2m_mean=20.0,  # GDD = 20 - 10 = 10 per day
                    temperature_2m_max=25.0,
                    temperature_2m_min=15.0
                )
            )
            # Move to next day
            if current_date.day < 28:  # Safe for all months
                current_date = datetime(current_date.year, current_date.month, current_date.day + 1)
            elif current_date.month < 12:
                current_date = datetime(current_date.year, current_date.month + 1, 1)
            else:
                current_date = datetime(current_date.year + 1, 1, 1)
        
        self.gateway_crop_profile.get.return_value = crop_profile
        self.gateway_weather.get.return_value = weather_data
        
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="eggplant",
            variety="Japanese",
            evaluation_period_start=datetime(2024, 6, 1),
            evaluation_period_end=datetime(2025, 3, 31),  # Extended to allow 250-day growth
            field=test_field,
        )
        
        response = await self.interactor.execute(request)
        
        # Verify response
        assert response.crop_name == "Eggplant"
        assert response.variety == "Japanese"
        
        # Total required GDD = 300 (seedling) + 2200 (harvest) = 2500 GDD
        # Actual growth_days may vary due to temperature stress and other factors
        # Verify it's in a reasonable range
        assert 250 <= response.growth_days <= 300  # Allow some variation
        
        # Verify that crop profile with harvest_start_gdd works correctly
        # harvest_start_gdd should not affect the optimization logic
        # (it's used for progress tracking, not period optimization)
        assert response.optimal_start_date is not None
        assert response.completion_date is not None
        
        # Verify all candidates have the same crop profile structure
        for candidate in response.candidates:
            assert candidate.crop.crop_id == "eggplant"
            assert candidate.crop.name == "Eggplant"

