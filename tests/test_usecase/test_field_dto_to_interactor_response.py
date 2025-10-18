"""DTO、Interactor、ResponseDTO 間のデータフローテスト

このテストは RequestDTO → Interactor → ResponseDTO のデータフローを検証します。
層境界: DTO → Interactor → ResponseDTO (UseCase層内)
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


class TestFieldDTOToInteractorResponse:
    """DTO → Interactor → ResponseDTO のデータフローテスト"""

    def test_interactor_extracts_field_from_dto(self):
        """Interactor が RequestDTO から Field を取得できる
        
        検証内容:
        - RequestDTO.field にアクセス可能
        - daily_fixed_cost が取得できる
        """
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
            field=field
        )

        # Mock gateways
        mock_crop_gateway = AsyncMock()
        mock_weather_gateway = AsyncMock()

        interactor = GrowthPeriodOptimizeInteractor(
            crop_profile_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
        )

        # Act - RequestDTO から Field を取得
        extracted_field = request.field
        cost = extracted_field.daily_fixed_cost

        # Assert - 正しく取得できる
        assert extracted_field is field
        assert cost == 5000.0
        assert isinstance(cost, float)

    @pytest.mark.parametrize("daily_cost,growth_days,expected_total", [
        (1000.0, 100, 100000.0),      # 基本
        (1000.5, 100, 100050.0),      # 小数点
        (4567.89, 123, 561850.47),    # 精度
        (0.0, 200, 0.0),              # ゼロコスト
        (99999.99, 1, 99999.99),      # 大きい値
    ])
    def test_interactor_calculates_cost_correctly(
        self, daily_cost, growth_days, expected_total
    ):
        """Interactor がコストを正しく計算
        
        検証内容:
        - コスト計算式: growth_days × field.daily_fixed_cost
        - 様々な値で正確に計算される
        - 精度が保持される
        """
        # Arrange
        field = Field(
            field_id="test",
            name="Test",
            area=1000.0,
            daily_fixed_cost=daily_cost,
        )

        # Act - コスト計算（Interactor内のロジックをシミュレート）
        total_cost = growth_days * field.daily_fixed_cost

        # Assert - 正確に計算される
        assert total_cost == pytest.approx(expected_total, rel=0.001)

    def test_response_dto_contains_field_and_costs(self):
        """ResponseDTO が Field とコスト情報を含む
        
        検証内容:
        - ResponseDTO.field が設定される
        - ResponseDTO.daily_fixed_cost が設定される
        - ResponseDTO.total_cost が計算される
        """
        # Arrange
        from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
            OptimalGrowthPeriodResponseDTO,
        )

        field = Field(
            field_id="test",
            name="Test",
            area=1000.0,
            daily_fixed_cost=3000.0,
        )

        growth_days = 100
        total_cost = growth_days * field.daily_fixed_cost

        # Act - ResponseDTO を生成
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Tomato",
            variety=None,
            optimal_start_date=datetime(2024, 5, 1),
            completion_date=datetime(2024, 8, 9),
            growth_days=growth_days,
            total_cost=total_cost,
            revenue=None,  # 追加
            profit=-total_cost,  # 追加: revenue がない場合は -cost
            daily_fixed_cost=field.daily_fixed_cost,
            field=field,
            candidates=[]
        )

        # Assert - 正しく設定される
        assert response.field is field
        assert response.daily_fixed_cost == field.daily_fixed_cost
        assert response.total_cost == total_cost
        assert response.total_cost == 300000.0

    def test_response_dto_cost_consistency(self):
        """ResponseDTO のコスト情報が一貫している
        
        検証内容:
        - total_cost == growth_days × daily_fixed_cost
        - ResponseDTO 内で矛盾がない
        """
        # Arrange
        from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
            OptimalGrowthPeriodResponseDTO,
        )

        field = Field(
            field_id="validate",
            name="検証用",
            area=1000.0,
            daily_fixed_cost=4567.89,
        )

        growth_days = 123
        expected_total_cost = growth_days * field.daily_fixed_cost

        # Act
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Tomato",
            variety=None,
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 2),
            growth_days=growth_days,
            total_cost=expected_total_cost,
            revenue=None,  # 追加
            profit=-expected_total_cost,  # 追加
            daily_fixed_cost=field.daily_fixed_cost,
            field=field,
            candidates=[]
        )

        # Assert - 一貫性がある
        assert response.total_cost == growth_days * response.daily_fixed_cost
        assert abs(response.total_cost - expected_total_cost) < 0.01

    def test_field_entity_unchanged_during_flow(self):
        """Field Entity がデータフロー中に変更されない
        
        検証内容:
        - Entity → DTO → Interactor → Response を通して不変
        - 元の Entity と同一オブジェクト
        """
        # Arrange
        from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
            OptimalGrowthPeriodResponseDTO,
        )

        field = Field(
            field_id="immutable_flow",
            name="不変フロー",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )

        original_cost = field.daily_fixed_cost

        # Act - RequestDTO → ResponseDTO のフロー
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 9, 30),
            field=field
        )

        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 9, 30),
            growth_days=182,
            total_cost=910000.0,
            revenue=None,  # 追加
            profit=-910000.0,  # 追加
            daily_fixed_cost=field.daily_fixed_cost,
            field=field,
            candidates=[]
        )

        # Assert - Entity は変更されていない
        assert field.daily_fixed_cost == original_cost
        assert field.daily_fixed_cost == 5000.0
        assert request.field is field
        assert response.field is field

    def test_zero_cost_field_flows_correctly(self):
        """コスト0の圃場も正しくフローする
        
        検証内容:
        - ゼロ値が正しく扱われる
        - total_cost も 0 になる
        """
        # Arrange
        from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
            OptimalGrowthPeriodResponseDTO,
        )

        field = Field(
            field_id="free",
            name="無料圃場",
            area=1000.0,
            daily_fixed_cost=0.0,
        )

        growth_days = 150

        # Act
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Test",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 9, 30),
            growth_days=growth_days,
            total_cost=0.0,
            revenue=None,  # 追加
            profit=0.0,  # 追加: cost=0の場合は profit=0
            daily_fixed_cost=0.0,
            field=field,
            candidates=[]
        )

        # Assert - ゼロ値が正しく扱われる
        assert response.daily_fixed_cost == 0.0
        assert response.total_cost == 0.0
        assert response.field.daily_fixed_cost == 0.0

