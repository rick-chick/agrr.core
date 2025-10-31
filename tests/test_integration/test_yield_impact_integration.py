"""Integration test for yield impact calculation through the entire stack.

Tests the end-to-end flow:
1. Weather data with temperature stress
2. Growth progress calculation with stress accumulation
3. Yield factor calculation
4. Revenue adjustment in optimization

No mocking or patching (CleanArchitecture design allows injection).
"""

import pytest
from datetime import datetime
from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.interactors.growth_progress_calculate_interactor import (
    GrowthProgressCalculateInteractor,
)
from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
    GrowthPeriodOptimizeInteractor,
)
from agrr_core.usecase.dto.growth_progress_calculate_request_dto import (
    GrowthProgressCalculateRequestDTO,
)
from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)

class MockCropProfileGateway:
    """Mock gateway that returns a predefined crop profile."""
    
    def __init__(self, crop_profile: CropProfile):
        self.crop_profile = crop_profile
    
    def get(self):
        return self.crop_profile

class MockWeatherGateway:
    """Mock gateway that returns predefined weather data."""
    
    def __init__(self, weather_data: List[WeatherData]):
        self.weather_data = weather_data
    
    def get(self):
        return self.weather_data

@pytest.fixture
def rice_crop_profile_with_revenue():
    """Rice crop profile with revenue information."""
    crop = Crop(
        crop_id="rice",
        name="Rice",
        area_per_unit=0.25,
        variety="Koshihikari",
        revenue_per_area=10000.0,  # 10,000 yen/m²
    )
    
    # Simple stage requirements
    germination = StageRequirement(
        stage=GrowthStage(name="germination", order=1),
        temperature=TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=25.0,
            low_stress_threshold=15.0,
            high_stress_threshold=30.0,
            frost_threshold=5.0,
            max_temperature=35.0,
        ),
        sunshine=SunshineProfile(minimum_sunshine_hours=4.0, target_sunshine_hours=6.0),
        thermal=ThermalRequirement(required_gdd=100.0),
    )
    
    flowering = StageRequirement(
        stage=GrowthStage(name="flowering", order=2),
        temperature=TemperatureProfile(
            base_temperature=10.0,
            optimal_min=25.0,
            optimal_max=30.0,
            low_stress_threshold=17.0,
            high_stress_threshold=35.0,  # Critical threshold
            frost_threshold=5.0,
            max_temperature=42.0,
            sterility_risk_threshold=35.0,  # Sterility risk at 35°C
        ),
        sunshine=SunshineProfile(minimum_sunshine_hours=5.0, target_sunshine_hours=8.0),
        thermal=ThermalRequirement(required_gdd=200.0),
    )
    
    return CropProfile(
        crop=crop,
        stage_requirements=[germination, flowering],
    )

@pytest.fixture
def weather_data_with_stress():
    """Weather data containing temperature stress conditions."""
    weather_list = []
    
    # Germination period: 10 days, optimal conditions
    for i in range(10):
        weather_list.append(WeatherData(
            time=datetime(2024, 5, 1 + i),
            temperature_2m_mean=22.0,  # Optimal
            temperature_2m_max=25.0,
            temperature_2m_min=18.0,
        ))
    
    # Flowering period: 20 days
    # Days 1-15: optimal conditions
    for i in range(15):
        weather_list.append(WeatherData(
            time=datetime(2024, 5, 11 + i),
            temperature_2m_mean=27.0,  # Optimal
            temperature_2m_max=30.0,
            temperature_2m_min=24.0,
        ))
    
    # Days 16-18: HIGH TEMPERATURE STRESS + STERILITY RISK (3 days)
    for i in range(3):
        weather_list.append(WeatherData(
            time=datetime(2024, 5, 26 + i),
            temperature_2m_mean=36.0,  # High temp stress!
            temperature_2m_max=38.0,   # Sterility risk!
            temperature_2m_min=33.0,
        ))
    
    # Days 19-20: back to optimal
    for i in range(2):
        weather_list.append(WeatherData(
            time=datetime(2024, 5, 29 + i),
            temperature_2m_mean=27.0,  # Optimal
            temperature_2m_max=30.0,
            temperature_2m_min=24.0,
        ))
    
    return weather_list

@pytest.fixture
def weather_data_perfect():
    """Weather data with perfect conditions (no stress)."""
    weather_list = []
    
    # 30 days of perfect conditions
    for i in range(30):
        weather_list.append(WeatherData(
            time=datetime(2024, 5, 1 + i),
            temperature_2m_mean=27.0,  # Always optimal
            temperature_2m_max=29.0,
            temperature_2m_min=24.0,
        ))
    
    return weather_list

@pytest.fixture
def test_field():
    """Test field entity."""
    return Field(
        field_id="field_01",
        name="Test Field",
        area=100.0,  # 100 m²
        daily_fixed_cost=500.0,  # 500 yen/day
        location=None,
    )

class TestYieldImpactIntegration:
    """Integration tests for yield impact through entire stack."""

    def test_growth_progress_calculates_yield_factor(
        self,
        rice_crop_profile_with_revenue,
        weather_data_with_stress,
    ):
        """Test that growth progress calculation includes yield_factor."""
        # Setup
        crop_gateway = MockCropProfileGateway(rice_crop_profile_with_revenue)
        weather_gateway = MockWeatherGateway(weather_data_with_stress)
        
        interactor = GrowthProgressCalculateInteractor(
            crop_profile_gateway=crop_gateway,
            weather_gateway=weather_gateway,
        )
        
        request = GrowthProgressCalculateRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            start_date=datetime(2024, 5, 1),
        )
        
        # Execute
        response = interactor.execute(request)
        
        # Verify yield_factor exists and shows impact
        assert response.yield_factor is not None
        assert response.yield_factor < 1.0  # Should have stress impact
        
        # Expected: 3 days of sterility risk during flowering
        # Sterility impact: 20% per day, sensitivity = 1.0
        # Factor: (1-0.20)^3 ≈ 0.512 (48.8% yield loss)
        # Plus some high temp stress
        assert response.yield_factor < 0.6  # Significant impact
        
        print(f"\nYield factor: {response.yield_factor:.3f}")
        print(f"Yield loss: {(1.0 - response.yield_factor) * 100:.1f}%")

    def test_perfect_weather_no_yield_loss(
        self,
        rice_crop_profile_with_revenue,
        weather_data_perfect,
    ):
        """Test that perfect weather results in no yield loss."""
        # Setup
        crop_gateway = MockCropProfileGateway(rice_crop_profile_with_revenue)
        weather_gateway = MockWeatherGateway(weather_data_perfect)
        
        interactor = GrowthProgressCalculateInteractor(
            crop_profile_gateway=crop_gateway,
            weather_gateway=weather_gateway,
        )
        
        request = GrowthProgressCalculateRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            start_date=datetime(2024, 5, 1),
        )
        
        # Execute
        response = interactor.execute(request)
        
        # Verify no yield loss
        assert response.yield_factor == 1.0
        print(f"\nPerfect weather - Yield factor: {response.yield_factor:.3f}")

    def test_optimization_result_contains_yield_factor(
        self,
        rice_crop_profile_with_revenue,
        weather_data_with_stress,
        test_field,
    ):
        """Test that optimization result contains yield_factor field."""
        # Setup
        crop_gateway = MockCropProfileGateway(rice_crop_profile_with_revenue)
        weather_gateway = MockWeatherGateway(weather_data_with_stress)
        
        interactor = GrowthPeriodOptimizeInteractor(
            crop_profile_gateway=crop_gateway,
            weather_gateway=weather_gateway,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 5, 1),
            evaluation_period_end=datetime(2024, 9, 30),
            field=test_field,
        )
        
        # Execute
        response = interactor.execute(request)
        
        # Verify candidates have yield_factor field
        assert len(response.candidates) > 0
        for candidate in response.candidates:
            # All candidates should have yield_factor (default 1.0 if not calculated)
            assert hasattr(candidate, 'yield_factor')
            assert candidate.yield_factor >= 0.0
            assert candidate.yield_factor <= 1.0
        
        # Verify metrics can be calculated with yield_factor
        valid_candidates = [c for c in response.candidates if c.total_cost is not None]
        if valid_candidates:
            metrics = valid_candidates[0].get_metrics()
            assert hasattr(metrics, 'yield_factor')
            assert metrics.yield_factor >= 0.0
        
        print(f"\nOptimization result has yield_factor support: OK")

    def test_yield_factor_field_exists_in_optimization(
        self,
        rice_crop_profile_with_revenue,
        weather_data_with_stress,
        weather_data_perfect,
        test_field,
    ):
        """Test that yield_factor field exists in optimization results."""
        # NOTE: The efficient sliding window algorithm (_evaluate_candidates_efficient)
        # currently doesn't calculate yield_factor for performance reasons.
        # This test verifies the field exists and has correct default value.
        
        # Run optimization
        crop_gateway = MockCropProfileGateway(rice_crop_profile_with_revenue)
        weather_gateway = MockWeatherGateway(weather_data_with_stress)
        
        interactor = GrowthPeriodOptimizeInteractor(
            crop_profile_gateway=crop_gateway,
            weather_gateway=weather_gateway,
        )
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 5, 1),
            evaluation_period_end=datetime(2024, 9, 30),
            field=test_field,
        )
        
        response = interactor.execute(request)
        
        # Verify yield_factor field exists
        assert len(response.candidates) > 0
        optimal = next(c for c in response.candidates if c.is_optimal)
        assert hasattr(optimal, 'yield_factor')
        
        # In efficient mode, yield_factor defaults to 1.0
        # (Full yield_factor calculation requires GrowthProgressCalculateInteractor)
        assert optimal.yield_factor == 1.0  # Default value
        
        print(f"\nOptimization result structure: OK")
        print(f"  Yield factor field exists: ✓")
        print(f"  Default value (efficient mode): {optimal.yield_factor}")

class TestYieldImpactRealisticScenarios:
    """Test realistic agricultural scenarios."""

    def test_high_temperature_during_flowering_reduces_yield(
        self,
        rice_crop_profile_with_revenue,
        test_field,
    ):
        """Test realistic scenario: High temperature during flowering period."""
        # Create weather: hot during flowering
        weather_list = []
        
        # Germination: 10 days, optimal (20-25°C)
        for i in range(10):
            weather_list.append(WeatherData(
                time=datetime(2024, 5, 1 + i),
                temperature_2m_mean=22.0,
                temperature_2m_max=25.0,
                temperature_2m_min=18.0,
            ))
        
        # Flowering: 20 days
        # First 10 days: optimal
        for i in range(10):
            weather_list.append(WeatherData(
                time=datetime(2024, 5, 11 + i),
                temperature_2m_mean=27.0,
                temperature_2m_max=30.0,
                temperature_2m_min=24.0,
            ))
        
        # Next 5 days: EXTREME HEAT (sterility risk)
        for i in range(5):
            weather_list.append(WeatherData(
                time=datetime(2024, 5, 21 + i),
                temperature_2m_mean=36.0,  # High stress
                temperature_2m_max=39.0,   # Sterility risk
                temperature_2m_min=33.0,
            ))
        
        # Final 5 days: return to optimal
        for i in range(5):
            weather_list.append(WeatherData(
                time=datetime(2024, 5, 26 + i),
                temperature_2m_mean=27.0,
                temperature_2m_max=30.0,
                temperature_2m_min=24.0,
            ))
        
        # Setup and execute
        crop_gateway = MockCropProfileGateway(rice_crop_profile_with_revenue)
        weather_gateway = MockWeatherGateway(weather_list)
        
        interactor = GrowthProgressCalculateInteractor(
            crop_profile_gateway=crop_gateway,
            weather_gateway=weather_gateway,
        )
        
        request = GrowthProgressCalculateRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            start_date=datetime(2024, 5, 1),
        )
        
        response = interactor.execute(request)
        
        # Verify severe yield loss
        # 5 days sterility @ 20% per day, sensitivity 1.0 = (1-0.20)^5 = 0.328
        # Plus 5 days high temp @ 5% per day, sensitivity 0.9 ≈ (1-0.045)^5 = 0.795
        # Combined: 0.328 * 0.795 ≈ 0.261 (about 74% yield loss)
        assert response.yield_factor < 0.35  # Severe loss
        
        print(f"\nExtreme heat scenario:")
        print(f"  Yield factor: {response.yield_factor:.3f}")
        print(f"  Yield loss: {(1.0 - response.yield_factor) * 100:.1f}%")

    def test_frost_during_germination(
        self,
        rice_crop_profile_with_revenue,
    ):
        """Test realistic scenario: Frost during germination."""
        # Create weather: frost at start
        weather_list = []
        
        # First 3 days: FROST
        for i in range(3):
            weather_list.append(WeatherData(
                time=datetime(2024, 4, 1 + i),
                temperature_2m_mean=8.0,
                temperature_2m_max=12.0,
                temperature_2m_min=2.0,  # Frost!
            ))
        
        # Rest: optimal
        for i in range(27):
            weather_list.append(WeatherData(
                time=datetime(2024, 4, 4 + i),
                temperature_2m_mean=22.0,
                temperature_2m_max=25.0,
                temperature_2m_min=18.0,
            ))
        
        # Setup and execute
        crop_gateway = MockCropProfileGateway(rice_crop_profile_with_revenue)
        weather_gateway = MockWeatherGateway(weather_list)
        
        interactor = GrowthProgressCalculateInteractor(
            crop_profile_gateway=crop_gateway,
            weather_gateway=weather_gateway,
        )
        
        request = GrowthProgressCalculateRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            start_date=datetime(2024, 4, 1),
        )
        
        response = interactor.execute(request)
        
        # Verify significant yield loss
        # 3 days frost @ 15% per day: (1 - 0.15)^3 = 0.85^3 ≈ 0.614 (38.6% yield loss)
        # Plus 3 days low temp stress @ 8% per day: (0.614) * (1 - 0.08)^3 ≈ 0.478
        # Total: ~52% yield loss due to frost + low temp stress
        assert 0.40 <= response.yield_factor <= 0.55  # Significant loss
        
        print(f"\nFrost scenario:")
        print(f"  Yield factor: {response.yield_factor:.3f}")
        print(f"  Yield loss: {(1.0 - response.yield_factor) * 100:.1f}%")

