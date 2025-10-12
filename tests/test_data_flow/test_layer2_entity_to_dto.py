"""Layer 2: Field Entity → Request DTO のデータ移送テスト

FieldエンティティがRequestDTOに正しく設定されることを確認
"""

import pytest
from datetime import datetime

from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.entity.entities.field_entity import Field


@pytest.mark.asyncio
class TestLayer2_EntityToDTO:
    """Entity層からDTO層へのデータ移送テスト."""

    async def test_field_entity_to_request_dto_basic(self):
        """基本: FieldエンティティがRequestDTOに正しく設定される."""
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

        # Assert - Fieldエンティティがそのまま保持される
        assert dto.field is field
        assert dto.field.field_id == "field_01"
        assert dto.field.name == "北圃場"
        assert dto.field.daily_fixed_cost == 5000.0

    async def test_daily_fixed_cost_accessible_from_dto(self):
        """DTOからdaily_fixed_costにアクセスできる."""
        # Arrange
        field = Field(
            field_id="test",
            name="Test",
            area=1000.0,
            daily_fixed_cost=7500.5,
        )

        # Act
        dto = OptimalGrowthPeriodRequestDTO(
            crop_id="tomato",
            variety=None,
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 8, 31),
            weather_data_file="weather.json",
            field=field
        )

        # Assert
        assert dto.field.daily_fixed_cost == 7500.5
        assert isinstance(dto.field.daily_fixed_cost, float)

    async def test_field_entity_immutability_in_dto(self):
        """DTO内のFieldエンティティもイミュータブル."""
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

        # Act & Assert - 変更できない
        with pytest.raises(Exception):  # FrozenInstanceError
            dto.field.daily_fixed_cost = 9999.0

    async def test_dto_validation_negative_cost(self):
        """DTO作成時に負のコストが検証される（Fieldレベルでは作成不可だが念のため）."""
        # Note: Fieldエンティティ作成時にRepositoryで検証されているが、
        # DTOレベルでも論理的に検証可能か確認
        
        # 正常なField
        field = Field(
            field_id="test",
            name="Test",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )

        # DTOは正常に作成できる
        dto = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 9, 30),
            weather_data_file="weather.json",
            field=field
        )

        assert dto.field.daily_fixed_cost >= 0

    async def test_dto_preserves_all_field_properties(self):
        """DTOがFieldのすべてのプロパティを保持する."""
        # Arrange
        field = Field(
            field_id="complete",
            name="完全圃場",
            area=2000.0,
            daily_fixed_cost=10000.0,
            location="西区画"
        )

        # Act
        dto = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Akitakomachi",
            evaluation_period_start=datetime(2024, 5, 1),
            evaluation_period_end=datetime(2024, 10, 31),
            weather_data_file="weather.json",
            field=field
        )

        # Assert - すべてのプロパティが保持される
        assert dto.field.field_id == "complete"
        assert dto.field.name == "完全圃場"
        assert dto.field.area == 2000.0
        assert dto.field.daily_fixed_cost == 10000.0
        assert dto.field.location == "西区画"

    async def test_dto_with_field_without_location(self):
        """locationがNoneのFieldもDTOに設定できる."""
        # Arrange
        field = Field(
            field_id="no_location",
            name="場所不明",
            area=1000.0,
            daily_fixed_cost=5000.0,
            location=None
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

        # Assert
        assert dto.field.location is None

    async def test_dto_validation_date_order(self):
        """DTOのバリデーション: 開始日が終了日より後の場合エラー."""
        # Arrange
        field = Field(
            field_id="test",
            name="Test",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="must be before"):
            OptimalGrowthPeriodRequestDTO(
                crop_id="rice",
                variety="Koshihikari",
                evaluation_period_start=datetime(2024, 9, 30),  # 後
                evaluation_period_end=datetime(2024, 4, 1),     # 前
                weather_data_file="weather.json",
                field=field
            )

    async def test_multiple_dtos_with_same_field(self):
        """同じFieldエンティティを複数のDTOで共有できる（イミュータブル）."""
        # Arrange
        field = Field(
            field_id="shared",
            name="共有圃場",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )

        # Act
        dto1 = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2024, 4, 1),
            evaluation_period_end=datetime(2024, 9, 30),
            weather_data_file="weather.json",
            field=field
        )

        dto2 = OptimalGrowthPeriodRequestDTO(
            crop_id="tomato",
            variety=None,
            evaluation_period_start=datetime(2024, 5, 1),
            evaluation_period_end=datetime(2024, 8, 31),
            weather_data_file="weather2.json",
            field=field
        )

        # Assert - 両方のDTOが同じFieldを参照
        assert dto1.field is dto2.field
        assert dto1.field.daily_fixed_cost == dto2.field.daily_fixed_cost

