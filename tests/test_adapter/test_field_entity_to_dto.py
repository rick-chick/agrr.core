"""Entity と DTO 間のデータマッピングテスト

このテストは Field Entity が RequestDTO に正しくマッピングされるかを検証します。
層境界: Entity (Domain) → DTO (UseCase)
"""

import pytest
from datetime import datetime

from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.entity.entities.field_entity import Field


class TestFieldEntityToDTO:
    """Entity → DTO 境界のデータマッピングテスト"""

    def test_entity_maps_to_request_dto(self):
        """Field Entity が RequestDTO に正しくマッピングされる
        
        検証内容:
        - Entity が DTO に設定される
        - daily_fixed_cost にアクセス可能
        - 参照が保持される（コピーされない）
        """
        # Arrange
        field = Field(
            field_id="field_01",
            name="北圃場",
            area=1000.0,
            daily_fixed_cost=5000.0,
            location="北区画"
        )

        # Act
        dto = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 9, 30),
            weather_data_file="weather.json",
            field=field
        )

        # Assert - Entity が正しくマッピングされる
        assert dto.field is field  # 同一オブジェクト
        assert dto.field.field_id == "field_01"
        assert dto.field.name == "北圃場"
        assert dto.field.daily_fixed_cost == 5000.0
        assert isinstance(dto.field.daily_fixed_cost, float)

    def test_entity_remains_immutable_in_dto(self):
        """DTO 内の Field Entity も不変
        
        検証内容:
        - DTO に設定された後も Entity は不変
        - UseCase 層で Entity が変更されない保証
        """
        # Arrange
        field = Field(
            field_id="immutable",
            name="不変",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )

        dto = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 9, 30),
            weather_data_file="weather.json",
            field=field
        )

        # Act & Assert - DTO 内でも不変
        with pytest.raises(Exception):  # FrozenInstanceError
            dto.field.daily_fixed_cost = 9999.0

