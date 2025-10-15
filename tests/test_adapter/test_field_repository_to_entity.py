"""Repository と Entity 間のデータ変換テスト

このテストは FieldFileRepository が Field Entity を正しく生成するかを検証します。
層境界: Repository (Adapter) → Entity (Domain)
"""

import pytest
import tempfile
import json
from pathlib import Path

from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway as FieldFileRepository
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.exceptions.file_error import FileError
from agrr_core.framework.services.io.file_service import FileService


@pytest.fixture
def temp_dir():
    """テスト用一時ディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def repository():
    """FieldFileRepository インスタンス"""
    file_repo = FileService()
    return FieldFileRepository(file_repository=file_repo)


class TestFieldRepositoryToEntity:
    """Repository → Entity 境界のデータ変換テスト"""

    @pytest.mark.asyncio
    async def test_repository_creates_valid_field_entity(self, repository, temp_dir):
        """Repository が有効な Field Entity を生成
        
        検証内容:
        - JSON から Field Entity への変換
        - daily_fixed_cost が正しく設定される
        - 型が正しい（float）
        - Entity がイミュータブル
        """
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

        # Assert - 正しい Entity が生成される
        assert isinstance(field, Field)
        assert field.field_id == "field_01"
        assert field.name == "北圃場"
        assert field.area == 1000.0
        assert field.daily_fixed_cost == 5000.0
        assert isinstance(field.daily_fixed_cost, float)
        assert field.location == "北区画"

    @pytest.mark.asyncio
    async def test_repository_validates_negative_cost(self, repository, temp_dir):
        """Repository が負のコストを拒否
        
        検証内容:
        - Repository 層でバリデーションが実行される
        - 不正なデータは Entity 層に到達しない
        """
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "negative",
            "name": "負コスト圃場",
            "area": 1000.0,
            "daily_fixed_cost": -1000.0,  # 負の値
        }
        field_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding='utf-8')

        # Act & Assert - Repository 層でエラー
        with pytest.raises(FileError, match="must be non-negative"):
            await repository.read_fields_from_file(str(field_file))

    @pytest.mark.asyncio
    async def test_field_entity_is_immutable(self, repository, temp_dir):
        """生成された Field Entity が不変
        
        検証内容:
        - frozen dataclass として動作
        - 値の変更が不可
        """
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

        # Assert - イミュータブル
        with pytest.raises(Exception):  # FrozenInstanceError
            field.daily_fixed_cost = 9999.0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("cost", [
        0.0,        # 最小値
        5000.0,     # 通常値
        5432.10,    # 小数点
        999999.99,  # 大きい値
    ])
    async def test_repository_preserves_cost_precision(self, repository, temp_dir, cost):
        """Repository がコストの精度を保持
        
        検証内容:
        - 様々な値が正しく Entity に設定される
        - 小数点精度が保持される
        - 型変換が正しい
        """
        # Arrange
        field_file = temp_dir / "field.json"
        json_data = {
            "field_id": "test",
            "name": "Test",
            "area": 1000.0,
            "daily_fixed_cost": cost,
        }
        field_file.write_text(json.dumps(json_data), encoding='utf-8')

        # Act
        fields = await repository.read_fields_from_file(str(field_file))
        field = fields[0]

        # Assert - 精度が保持される
        assert field.daily_fixed_cost == cost
        assert isinstance(field.daily_fixed_cost, float)

