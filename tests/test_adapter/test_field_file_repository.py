"""Tests for FieldFileGateway (Adapter layer)."""

import pytest
from pathlib import Path
import tempfile
import json

from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.exceptions.file_error import FileError

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def file_repository():
    """Create a file repository for testing."""
    from agrr_core.framework.services.io.file_service import FileService
    return FileService()

@pytest.fixture
def field_file_repository(file_repository):
    """Create a field file gateway for testing."""
    return FieldFileGateway(file_repository=file_repository)

class TestFieldFileGateway:
    """Test cases for FieldFileGateway."""

    def test_read_single_field_json(self, field_file_repository, temp_dir):
        """Test reading a single field from JSON file."""
        # Arrange
        test_file = temp_dir / "test_field.json"
        field_data = {
            "field_id": "field_01",
            "name": "北圃場",
            "area": 1000.0,
            "daily_fixed_cost": 5000.0,
            "location": "北区画"
        }
        test_file.write_text(json.dumps(field_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = field_file_repository.read_fields_from_file(str(test_file))

        # Assert
        assert len(fields) == 1
        field = fields[0]
        assert field.field_id == "field_01"
        assert field.name == "北圃場"
        assert field.area == 1000.0
        assert field.daily_fixed_cost == 5000.0
        assert field.location == "北区画"

    def test_read_multiple_fields_json(self, field_file_repository, temp_dir):
        """Test reading multiple fields from JSON file."""
        # Arrange
        test_file = temp_dir / "test_fields.json"
        fields_data = {
            "fields": [
                {
                    "field_id": "field_01",
                    "name": "北圃場",
                    "area": 1000.0,
                    "daily_fixed_cost": 5000.0,
                    "location": "北区画"
                },
                {
                    "field_id": "field_02",
                    "name": "南圃場",
                    "area": 1500.0,
                    "daily_fixed_cost": 7000.0,
                    "location": "南区画"
                }
            ]
        }
        test_file.write_text(json.dumps(fields_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = field_file_repository.read_fields_from_file(str(test_file))

        # Assert
        assert len(fields) == 2
        assert fields[0].field_id == "field_01"
        assert fields[0].daily_fixed_cost == 5000.0
        assert fields[1].field_id == "field_02"
        assert fields[1].daily_fixed_cost == 7000.0

    def test_get_field_by_id(self, field_file_repository, temp_dir):
        """Test getting a specific field by ID."""
        # Arrange
        test_file = temp_dir / "test_fields.json"
        fields_data = {
            "fields": [
                {
                    "field_id": "field_01",
                    "name": "北圃場",
                    "area": 1000.0,
                    "daily_fixed_cost": 5000.0
                },
                {
                    "field_id": "field_02",
                    "name": "南圃場",
                    "area": 1500.0,
                    "daily_fixed_cost": 7000.0
                }
            ]
        }
        test_file.write_text(json.dumps(fields_data, ensure_ascii=False), encoding='utf-8')

        # Act
        field = field_file_repository.get_field_by_id(str(test_file), "field_02")

        # Assert
        assert field is not None
        assert field.field_id == "field_02"
        assert field.name == "南圃場"
        assert field.daily_fixed_cost == 7000.0

    def test_get_field_by_id_not_found(self, field_file_repository, temp_dir):
        """Test getting a field that doesn't exist."""
        # Arrange
        test_file = temp_dir / "test_fields.json"
        fields_data = {
            "fields": [
                {
                    "field_id": "field_01",
                    "name": "北圃場",
                    "area": 1000.0,
                    "daily_fixed_cost": 5000.0
                }
            ]
        }
        test_file.write_text(json.dumps(fields_data, ensure_ascii=False), encoding='utf-8')

        # Act
        field = field_file_repository.get_field_by_id(str(test_file), "field_99")

        # Assert
        assert field is None

    def test_read_fields_with_optional_location(self, field_file_repository, temp_dir):
        """Test reading fields with optional location field."""
        # Arrange
        test_file = temp_dir / "test_fields.json"
        fields_data = {
            "fields": [
                {
                    "field_id": "field_01",
                    "name": "北圃場",
                    "area": 1000.0,
                    "daily_fixed_cost": 5000.0
                    # location is optional
                }
            ]
        }
        test_file.write_text(json.dumps(fields_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = field_file_repository.read_fields_from_file(str(test_file))

        # Assert
        assert len(fields) == 1
        assert fields[0].location is None

    def test_read_fields_file_not_found(self, field_file_repository):
        """Test reading from non-existent file."""
        # Act & Assert
        with pytest.raises(FileError, match="File not found"):
            field_file_repository.read_fields_from_file("/nonexistent/file.json")

    def test_read_fields_invalid_json(self, field_file_repository, temp_dir):
        """Test reading invalid JSON."""
        # Arrange
        test_file = temp_dir / "invalid.json"
        test_file.write_text("{ invalid json }", encoding='utf-8')

        # Act & Assert
        with pytest.raises(FileError):
            field_file_repository.read_fields_from_file(str(test_file))

    def test_read_fields_missing_required_field(self, field_file_repository, temp_dir):
        """Test reading fields with missing required fields."""
        # Arrange
        test_file = temp_dir / "test_fields.json"
        fields_data = {
            "fields": [
                {
                    "field_id": "field_01",
                    "name": "北圃場"
                    # Missing area and daily_fixed_cost
                }
            ]
        }
        test_file.write_text(json.dumps(fields_data, ensure_ascii=False), encoding='utf-8')

        # Act & Assert
        with pytest.raises(FileError, match="Missing required field"):
            field_file_repository.read_fields_from_file(str(test_file))

    def test_validate_field_data_valid(self, field_file_repository):
        """Test validation of valid field data."""
        # Arrange
        field_data = {
            "field_id": "field_01",
            "name": "北圃場",
            "area": 1000.0,
            "daily_fixed_cost": 5000.0
        }

        # Act
        result = field_file_repository.validate_field_data(field_data)

        # Assert
        assert result is True

    def test_validate_field_data_missing_required(self, field_file_repository):
        """Test validation of field data with missing required fields."""
        # Arrange
        field_data = {
            "field_id": "field_01",
            "name": "北圃場"
            # Missing area and daily_fixed_cost
        }

        # Act
        result = field_file_repository.validate_field_data(field_data)

        # Assert
        assert result is False

    def test_validate_field_data_negative_values(self, field_file_repository):
        """Test validation rejects negative values for area and cost."""
        # Arrange
        field_data = {
            "field_id": "field_01",
            "name": "北圃場",
            "area": -1000.0,
            "daily_fixed_cost": -5000.0
        }

        # Act
        result = field_file_repository.validate_field_data(field_data)

        # Assert
        assert result is False

    def test_get_method_with_file_path(self, file_repository, temp_dir):
        """Test get method (FieldRepositoryInterface implementation)."""
        # Arrange
        test_file = temp_dir / "test_fields.json"
        fields_data = {
            "fields": [
                {
                    "field_id": "field_01",
                    "name": "北圃場",
                    "area": 1000.0,
                    "daily_fixed_cost": 5000.0
                },
                {
                    "field_id": "field_02",
                    "name": "南圃場",
                    "area": 1500.0,
                    "daily_fixed_cost": 7000.0
                }
            ]
        }
        test_file.write_text(json.dumps(fields_data, ensure_ascii=False), encoding='utf-8')
        
        # Create repository with file_path
        repository = FieldFileGateway(file_repository=file_repository, file_path=str(test_file))

        # Act
        field = repository.get("field_02")

        # Assert
        assert field is not None
        assert field.field_id == "field_02"
        assert field.name == "南圃場"
        assert field.daily_fixed_cost == 7000.0

    def test_get_method_not_found(self, file_repository, temp_dir):
        """Test get method returns None for non-existent field."""
        # Arrange
        test_file = temp_dir / "test_fields.json"
        fields_data = {
            "fields": [
                {
                    "field_id": "field_01",
                    "name": "北圃場",
                    "area": 1000.0,
                    "daily_fixed_cost": 5000.0
                }
            ]
        }
        test_file.write_text(json.dumps(fields_data, ensure_ascii=False), encoding='utf-8')
        
        # Create repository with file_path
        repository = FieldFileGateway(file_repository=file_repository, file_path=str(test_file))

        # Act
        field = repository.get("field_99")

        # Assert
        assert field is None

    def test_read_field_with_default_fallow_period(self, field_file_repository, temp_dir):
        """Test reading field without fallow_period_days uses default value."""
        # Arrange
        test_file = temp_dir / "test_field.json"
        field_data = {
            "field_id": "field_01",
            "name": "北圃場",
            "area": 1000.0,
            "daily_fixed_cost": 5000.0
            # fallow_period_days not specified
        }
        test_file.write_text(json.dumps(field_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = field_file_repository.read_fields_from_file(str(test_file))

        # Assert
        assert len(fields) == 1
        field = fields[0]
        assert field.fallow_period_days == 28  # Default value

    def test_read_field_with_custom_fallow_period(self, field_file_repository, temp_dir):
        """Test reading field with custom fallow_period_days."""
        # Arrange
        test_file = temp_dir / "test_field.json"
        field_data = {
            "field_id": "field_01",
            "name": "北圃場",
            "area": 1000.0,
            "daily_fixed_cost": 5000.0,
            "fallow_period_days": 14
        }
        test_file.write_text(json.dumps(field_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = field_file_repository.read_fields_from_file(str(test_file))

        # Assert
        assert len(fields) == 1
        field = fields[0]
        assert field.fallow_period_days == 14

    def test_read_field_with_zero_fallow_period(self, field_file_repository, temp_dir):
        """Test reading field with zero fallow_period_days."""
        # Arrange
        test_file = temp_dir / "test_field.json"
        field_data = {
            "field_id": "field_01",
            "name": "北圃場",
            "area": 1000.0,
            "daily_fixed_cost": 5000.0,
            "fallow_period_days": 0
        }
        test_file.write_text(json.dumps(field_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = field_file_repository.read_fields_from_file(str(test_file))

        # Assert
        assert len(fields) == 1
        field = fields[0]
        assert field.fallow_period_days == 0

    def test_read_multiple_fields_with_different_fallow_periods(self, field_file_repository, temp_dir):
        """Test reading multiple fields with different fallow periods."""
        # Arrange
        test_file = temp_dir / "test_fields.json"
        fields_data = {
            "fields": [
                {
                    "field_id": "field_01",
                    "name": "北圃場",
                    "area": 1000.0,
                    "daily_fixed_cost": 5000.0,
                    "fallow_period_days": 14
                },
                {
                    "field_id": "field_02",
                    "name": "南圃場",
                    "area": 1500.0,
                    "daily_fixed_cost": 7000.0,
                    "fallow_period_days": 21
                },
                {
                    "field_id": "field_03",
                    "name": "東圃場",
                    "area": 800.0,
                    "daily_fixed_cost": 4000.0
                    # fallow_period_days not specified, should use default
                }
            ]
        }
        test_file.write_text(json.dumps(fields_data, ensure_ascii=False), encoding='utf-8')

        # Act
        fields = field_file_repository.read_fields_from_file(str(test_file))

        # Assert
        assert len(fields) == 3
        assert fields[0].fallow_period_days == 14
        assert fields[1].fallow_period_days == 21
        assert fields[2].fallow_period_days == 28  # Default

    def test_validate_field_data_with_valid_fallow_period(self, field_file_repository):
        """Test validation accepts valid fallow_period_days."""
        # Arrange
        field_data = {
            "field_id": "field_01",
            "name": "北圃場",
            "area": 1000.0,
            "daily_fixed_cost": 5000.0,
            "fallow_period_days": 21
        }

        # Act
        result = field_file_repository.validate_field_data(field_data)

        # Assert
        assert result is True

    def test_validate_field_data_with_negative_fallow_period(self, field_file_repository):
        """Test validation rejects negative fallow_period_days."""
        # Arrange
        field_data = {
            "field_id": "field_01",
            "name": "北圃場",
            "area": 1000.0,
            "daily_fixed_cost": 5000.0,
            "fallow_period_days": -10
        }

        # Act
        result = field_file_repository.validate_field_data(field_data)

        # Assert
        assert result is False

