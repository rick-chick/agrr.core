"""Layer 4: Response DTO のデータ移送テスト

ResponseDTOがFieldエンティティとコスト情報を保持することを確認
"""

import pytest
from datetime import datetime

from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    OptimalGrowthPeriodResponseDTO,
    CandidateResultDTO,
)
from agrr_core.entity.entities.field_entity import Field


class TestLayer4_ResponseDTO:
    """ResponseDTOのデータ保持テスト."""

    def test_response_dto_contains_field_entity(self):
        """ResponseDTOがFieldエンティティを保持する."""
        # Arrange
        field = Field(
            field_id="field_01",
            name="北圃場",
            area=1000.0,
            daily_fixed_cost=5000.0,
            location="北区画"
        )

        # Act
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 15),
            completion_date=datetime(2024, 9, 18),
            growth_days=156,
            total_cost=780000.0,
            daily_fixed_cost=5000.0,
            field=field,
            candidates=[]
        )

        # Assert
        assert response.field is field
        assert response.field.field_id == "field_01"
        assert response.field.name == "北圃場"
        assert response.field.daily_fixed_cost == 5000.0

    def test_response_dto_cost_consistency(self):
        """ResponseDTOのコスト情報が一貫している."""
        # Arrange
        field = Field(
            field_id="test",
            name="Test",
            area=1000.0,
            daily_fixed_cost=3000.0,
        )

        growth_days = 100
        total_cost = growth_days * field.daily_fixed_cost

        # Act
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Tomato",
            variety=None,
            optimal_start_date=datetime(2024, 5, 1),
            completion_date=datetime(2024, 8, 9),
            growth_days=growth_days,
            total_cost=total_cost,
            daily_fixed_cost=field.daily_fixed_cost,
            field=field,
            candidates=[]
        )

        # Assert - コストの一貫性
        assert response.daily_fixed_cost == field.daily_fixed_cost
        assert response.total_cost == growth_days * response.daily_fixed_cost
        assert response.total_cost == 300000.0

    def test_response_dto_preserves_all_field_info(self):
        """ResponseDTOがFieldのすべての情報を保持する."""
        # Arrange
        field = Field(
            field_id="complete",
            name="完全圃場",
            area=2000.0,
            daily_fixed_cost=10000.0,
            location="西区画"
        )

        # Act
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Akitakomachi",
            optimal_start_date=datetime(2024, 5, 1),
            completion_date=datetime(2024, 10, 15),
            growth_days=167,
            total_cost=1670000.0,
            daily_fixed_cost=10000.0,
            field=field,
            candidates=[]
        )

        # Assert - すべてのフィールド情報が保持される
        assert response.field.field_id == "complete"
        assert response.field.name == "完全圃場"
        assert response.field.area == 2000.0
        assert response.field.daily_fixed_cost == 10000.0
        assert response.field.location == "西区画"

    def test_response_dto_field_immutability(self):
        """ResponseDTO内のFieldもイミュータブル."""
        # Arrange
        field = Field(
            field_id="immutable",
            name="不変",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )

        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 9, 30),
            growth_days=182,
            total_cost=910000.0,
            daily_fixed_cost=5000.0,
            field=field,
            candidates=[]
        )

        # Act & Assert - 変更できない
        with pytest.raises(Exception):  # FrozenInstanceError
            response.field.daily_fixed_cost = 9999.0

    def test_response_dto_with_candidates(self):
        """候補リストを含むResponseDTO."""
        # Arrange
        field = Field(
            field_id="test",
            name="Test",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )

        candidates = [
            CandidateResultDTO(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 9, 15),
                growth_days=167,
                field=field,  # 167000 / 167 = 1000
                is_optimal=False
            ),
            CandidateResultDTO(
                start_date=datetime(2024, 4, 15),
                completion_date=datetime(2024, 9, 20),
                growth_days=158,
                field=field,  # 158000 / 158 = 1000
                is_optimal=True
            ),
        ]

        # Act
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 15),
            completion_date=datetime(2024, 9, 20),
            growth_days=158,
            total_cost=158000.0,
            daily_fixed_cost=1000.0,
            field=field,
            candidates=candidates
        )

        # Assert
        assert len(response.candidates) == 2
        assert response.candidates[1].is_optimal is True
        # 最適候補のコストがresponseのtotal_costと一致
        assert response.candidates[1].total_cost == response.total_cost

    def test_response_dto_cost_calculation_validation(self):
        """ResponseDTOのコスト計算が正しい."""
        # Arrange
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
            daily_fixed_cost=field.daily_fixed_cost,
            field=field,
            candidates=[]
        )

        # Assert
        assert response.total_cost == growth_days * response.daily_fixed_cost
        assert abs(response.total_cost - expected_total_cost) < 0.01

    def test_response_dto_zero_cost_field(self):
        """コスト0の圃場のResponseDTO."""
        # Arrange
        field = Field(
            field_id="free",
            name="無料圃場",
            area=1000.0,
            daily_fixed_cost=0.0,
        )

        # Act
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Test",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 9, 30),
            growth_days=182,
            total_cost=0.0,
            daily_fixed_cost=0.0,
            field=field,
            candidates=[]
        )

        # Assert
        assert response.daily_fixed_cost == 0.0
        assert response.total_cost == 0.0
        assert response.field.daily_fixed_cost == 0.0

    def test_response_dto_field_metadata_for_display(self):
        """表示用のフィールドメタデータが取得できる."""
        # Arrange
        field = Field(
            field_id="display_test",
            name="表示テスト圃場",
            area=1500.0,
            daily_fixed_cost=6000.0,
            location="東区画"
        )

        # Act
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 9, 30),
            growth_days=182,
            total_cost=1092000.0,
            daily_fixed_cost=6000.0,
            field=field,
            candidates=[]
        )

        # Assert - Presenter で使用する情報が取得できる
        assert response.field.name == "表示テスト圃場"
        assert response.field.field_id == "display_test"
        assert response.field.area == 1500.0
        assert response.field.location == "東区画"
        assert response.daily_fixed_cost == 6000.0
        assert response.total_cost == 1092000.0

