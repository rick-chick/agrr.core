"""Layer 1: Repository → Field Entity のデータ移送テスト

JSONファイルからFieldエンティティへの変換が正しく行われることを確認
"""

import pytest
import tempfile
import json
from pathlib import Path

from agrr_core.adapter.repositories.field_file_repository import FieldFileRepository
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.exceptions.file_error import FileError
from agrr_core.framework.repositories.file_repository import FileRepository


@pytest.fixture
def temp_dir():
    """テスト用一時ディレクトリ."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def repository():
    """FieldFileRepository インスタンス."""
    file_repo = FileRepository()
    return FieldFileRepository(file_repository=file_repo)


@pytest.mark.asyncio
class TestLayer1_RepositoryToEntity:
    """Repository層からEntity層へのデータ移送テスト."""

    async def test_json_to_field_entity_basic(self, repository, temp_dir):
        """基本: JSONの各フィールドがFieldエンティティに正しくマッピングされる."""
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "field_01",
            "name": "北圃場",
            "area": 1000.0,
            "daily_fixed_cost": 5000.0,
            "location": "北区画"
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = await repository.read_fields_from_file(str(field_file))
        field = fields[0]

        # Assert - 各フィールドが正確に移送される
        assert isinstance(field, Field)
        assert field.field_id == "field_01"
        assert field.name == "北圃場"
        assert field.area == 1000.0
        assert field.daily_fixed_cost == 5000.0
        assert field.location == "北区画"

    async def test_daily_fixed_cost_precision(self, repository, temp_dir):
        """daily_fixed_costの精度が保たれる（小数点）."""
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "test",
            "name": "Test",
            "area": 1000.0,
            "daily_fixed_cost": 5432.10,  # 小数点2桁
        }
        field_file.write_text(json.dumps(json_data), encoding='utf-8')

        # Act
        fields = await repository.read_fields_from_file(str(field_file))
        field = fields[0]

        # Assert
        assert field.daily_fixed_cost == 5432.10
        assert isinstance(field.daily_fixed_cost, float)

    async def test_daily_fixed_cost_zero(self, repository, temp_dir):
        """daily_fixed_cost=0.0 も正しく処理される."""
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "free_field",
            "name": "無料圃場",
            "area": 500.0,
            "daily_fixed_cost": 0.0,
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = await repository.read_fields_from_file(str(field_file))
        field = fields[0]

        # Assert
        assert field.daily_fixed_cost == 0.0

    async def test_daily_fixed_cost_large_value(self, repository, temp_dir):
        """大きな値のdaily_fixed_costも正しく処理される."""
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "expensive",
            "name": "高額圃場",
            "area": 10000.0,
            "daily_fixed_cost": 999999.99,
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = await repository.read_fields_from_file(str(field_file))
        field = fields[0]

        # Assert
        assert field.daily_fixed_cost == 999999.99

    async def test_location_optional(self, repository, temp_dir):
        """location が省略された場合、Noneになる."""
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "field_02",
            "name": "南圃場",
            "area": 1500.0,
            "daily_fixed_cost": 7000.0,
            # location なし
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = await repository.read_fields_from_file(str(field_file))
        field = fields[0]

        # Assert
        assert field.location is None

    async def test_missing_daily_fixed_cost_raises_error(self, repository, temp_dir):
        """必須フィールド daily_fixed_cost が欠けている場合エラー."""
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "incomplete",
            "name": "不完全圃場",
            "area": 1000.0,
            # daily_fixed_cost なし
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act & Assert
        with pytest.raises(FileError, match="Missing required field"):
            await repository.read_fields_from_file(str(field_file))

    async def test_negative_daily_fixed_cost_rejected(self, repository, temp_dir):
        """負のdaily_fixed_costは拒否される."""
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "negative",
            "name": "負コスト圃場",
            "area": 1000.0,
            "daily_fixed_cost": -1000.0,  # 負の値
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act & Assert
        with pytest.raises(FileError, match="must be non-negative"):
            await repository.read_fields_from_file(str(field_file))

    async def test_field_entity_immutability(self, repository, temp_dir):
        """Fieldエンティティはイミュータブル（frozen dataclass）."""
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "immutable_test",
            "name": "テスト",
            "area": 1000.0,
            "daily_fixed_cost": 5000.0,
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = await repository.read_fields_from_file(str(field_file))
        field = fields[0]

        # Assert - frozenなので変更不可
        with pytest.raises(Exception):  # FrozenInstanceError
            field.daily_fixed_cost = 9999.0

    async def test_single_field_json_format(self, repository, temp_dir):
        """単一フィールド形式のJSONが正しく読み込まれる."""
        # Arrange - fieldsキーなし、直接フィールドデータ
        field_file = temp_dir / "single_field.json"
        json_data = {
            "field_id": "single",
            "name": "単一圃場",
            "area": 800.0,
            "daily_fixed_cost": 4000.0,
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = await repository.read_fields_from_file(str(field_file))

        # Assert
        assert len(fields) == 1
        field = fields[0]
        assert field.field_id == "single"
        assert field.daily_fixed_cost == 4000.0

    async def test_type_conversion_string_to_float(self, repository, temp_dir):
        """文字列の数値がfloatに変換される."""
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "string_numbers",
            "name": "文字列数値",
            "area": "1000",  # 文字列
            "daily_fixed_cost": "5000.5",  # 文字列
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = await repository.read_fields_from_file(str(field_file))
        field = fields[0]

        # Assert
        assert isinstance(field.area, float)
        assert isinstance(field.daily_fixed_cost, float)
        assert field.area == 1000.0
        assert field.daily_fixed_cost == 5000.5

