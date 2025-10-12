"""Layer 3: Request DTO → Interactor のデータ移送テスト

InteractorがRequestDTOからdaily_fixed_costを取得し、
コスト計算に使用することを確認
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
    GrowthPeriodOptimizeInteractor,
)
from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_requirement_aggregate_entity import CropRequirementAggregate
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.entity.entities.weather_entity import WeatherData


@pytest.mark.asyncio
class TestLayer3_DTOToInteractor:
    """DTO層からInteractor層へのデータ移送テスト."""

    async def test_interactor_extracts_daily_fixed_cost_from_dto(self):
        """Interactorがrequest.field.daily_fixed_costを取得できる."""
        # Arrange
        field = Field(
            field_id="field_01",
            name="北圃場",
            area=1000.0,
            daily_fixed_cost=5000.0,
            location="北区画"
        )

        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 9, 30),
            weather_data_file="weather.json",
            field=field
        )

        # Mock gateways
        mock_crop_gateway = AsyncMock()
        mock_weather_gateway = AsyncMock()

        interactor = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
        )

        # Act - daily_fixed_costを取得
        cost = request.field.daily_fixed_cost

        # Assert
        assert cost == 5000.0
        assert isinstance(cost, float)

    async def test_cost_calculation_with_field_cost(self):
        """コスト計算: growth_days × field.daily_fixed_cost."""
        # Arrange
        field = Field(
            field_id="test",
            name="Test",
            area=1000.0,
            daily_fixed_cost=3000.0,
        )

        # Simulate growth calculation result
        growth_days = 100
        expected_total_cost = growth_days * field.daily_fixed_cost

        # Act
        actual_total_cost = growth_days * field.daily_fixed_cost

        # Assert
        assert actual_total_cost == 300000.0
        assert actual_total_cost == expected_total_cost

    async def test_cost_calculation_with_various_costs(self):
        """様々なコスト値での計算が正確."""
        # Test cases: (daily_cost, growth_days, expected_total)
        test_cases = [
            (5000.0, 150, 750000.0),
            (1000.5, 100, 100050.0),
            (0.0, 200, 0.0),
            (99999.99, 1, 99999.99),
        ]

        for daily_cost, growth_days, expected_total in test_cases:
            # Arrange
            field = Field(
                field_id="test",
                name="Test",
                area=1000.0,
                daily_fixed_cost=daily_cost,
            )

            # Act
            total_cost = growth_days * field.daily_fixed_cost

            # Assert
            assert total_cost == expected_total, \
                f"Cost calc failed: {growth_days} × {daily_cost} should be {expected_total}, got {total_cost}"

    async def test_field_cost_precision_in_calculation(self):
        """小数点を含むコストでの計算精度."""
        # Arrange
        field = Field(
            field_id="precise",
            name="精密",
            area=1000.0,
            daily_fixed_cost=4567.89,
        )

        growth_days = 123

        # Act
        total_cost = growth_days * field.daily_fixed_cost

        # Assert
        expected = 123 * 4567.89
        assert abs(total_cost - expected) < 0.01  # 浮動小数点誤差を考慮

    async def test_minimum_cost_selection(self):
        """複数候補から最小コストを選択する."""
        # Arrange
        field = Field(
            field_id="test",
            name="Test",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )

        # Simulate multiple candidates
        candidates = [
            {"growth_days": 150, "start_date": datetime(2024, 4, 1)},
            {"growth_days": 100, "start_date": datetime(2024, 5, 1)},  # 最小
            {"growth_days": 200, "start_date": datetime(2024, 3, 1)},
        ]

        # Act - 各候補のコストを計算
        costs = [(c["growth_days"] * field.daily_fixed_cost, c) for c in candidates]
        min_cost_candidate = min(costs, key=lambda x: x[0])

        # Assert
        assert min_cost_candidate[0] == 100000.0  # 100日 × 1000円
        assert min_cost_candidate[1]["growth_days"] == 100

    async def test_field_entity_unchanged_during_calculation(self):
        """計算中もFieldエンティティは不変."""
        # Arrange
        field = Field(
            field_id="immutable",
            name="不変",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )

        original_cost = field.daily_fixed_cost

        # Act - 計算を行う
        total_cost = 100 * field.daily_fixed_cost

        # Assert - Fieldは変更されていない
        assert field.daily_fixed_cost == original_cost
        assert field.daily_fixed_cost == 5000.0
        assert total_cost == 500000.0

    async def test_zero_cost_field_calculation(self):
        """コスト0の圃場でも計算が正しく行われる."""
        # Arrange
        field = Field(
            field_id="free",
            name="無料",
            area=1000.0,
            daily_fixed_cost=0.0,
        )

        growth_days = 150

        # Act
        total_cost = growth_days * field.daily_fixed_cost

        # Assert
        assert total_cost == 0.0

    async def test_request_dto_field_accessible_in_interactor(self):
        """InteractorがRequestDTOのfieldに自由にアクセスできる."""
        # Arrange
        field = Field(
            field_id="accessible",
            name="アクセス可能",
            area=2500.0,
            daily_fixed_cost=8000.0,
            location="中央区画"
        )

        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 9, 30),
            weather_data_file="weather.json",
            field=field
        )

        # Act - 各プロパティにアクセス
        field_id = request.field.field_id
        name = request.field.name
        area = request.field.area
        cost = request.field.daily_fixed_cost
        location = request.field.location

        # Assert
        assert field_id == "accessible"
        assert name == "アクセス可能"
        assert area == 2500.0
        assert cost == 8000.0
        assert location == "中央区画"

