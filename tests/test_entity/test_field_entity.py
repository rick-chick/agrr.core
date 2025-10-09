"""Tests for Field entity."""

import pytest
from agrr_core.entity.entities.field_entity import Field


class TestFieldEntity:
    """Test Field entity."""

    def test_field_creation_with_minimum_attributes(self):
        """Test Field creation with minimum required attributes."""
        field = Field(
            field_id="field_001",
            name="田んぼ1号",
            area=1000.0,
            daily_fixed_cost=5000.0
        )
        
        assert field.field_id == "field_001"
        assert field.name == "田んぼ1号"
        assert field.area == 1000.0
        assert field.daily_fixed_cost == 5000.0

    def test_field_creation_with_all_attributes(self):
        """Test Field creation with all attributes."""
        field = Field(
            field_id="field_002",
            name="畑A",
            area=2500.5,
            daily_fixed_cost=7500.0,
            location="北区画"
        )
        
        assert field.field_id == "field_002"
        assert field.name == "畑A"
        assert field.area == 2500.5
        assert field.daily_fixed_cost == 7500.0
        assert field.location == "北区画"

    def test_field_creation_without_optional_location(self):
        """Test Field creation without optional location."""
        field = Field(
            field_id="field_003",
            name="圃場X",
            area=500.0,
            daily_fixed_cost=3000.0
        )
        
        assert field.location is None

    def test_field_with_zero_daily_fixed_cost(self):
        """Test Field with zero daily fixed cost."""
        field = Field(
            field_id="field_004",
            name="無料圃場",
            area=100.0,
            daily_fixed_cost=0.0
        )
        
        assert field.daily_fixed_cost == 0.0

    def test_field_immutability(self):
        """Test that Field is immutable (frozen dataclass)."""
        field = Field(
            field_id="field_005",
            name="不変圃場",
            area=1500.0,
            daily_fixed_cost=6000.0
        )
        
        with pytest.raises(AttributeError):
            field.daily_fixed_cost = 7000.0

    def test_field_equality(self):
        """Test Field equality based on all attributes."""
        field1 = Field(
            field_id="field_006",
            name="圃場A",
            area=1000.0,
            daily_fixed_cost=5000.0
        )
        field2 = Field(
            field_id="field_006",
            name="圃場A",
            area=1000.0,
            daily_fixed_cost=5000.0
        )
        
        assert field1 == field2

    def test_field_inequality_different_id(self):
        """Test Field inequality when field_id differs."""
        field1 = Field(
            field_id="field_007",
            name="圃場A",
            area=1000.0,
            daily_fixed_cost=5000.0
        )
        field2 = Field(
            field_id="field_008",
            name="圃場A",
            area=1000.0,
            daily_fixed_cost=5000.0
        )
        
        assert field1 != field2

    def test_field_inequality_different_cost(self):
        """Test Field inequality when daily_fixed_cost differs."""
        field1 = Field(
            field_id="field_009",
            name="圃場A",
            area=1000.0,
            daily_fixed_cost=5000.0
        )
        field2 = Field(
            field_id="field_009",
            name="圃場A",
            area=1000.0,
            daily_fixed_cost=6000.0
        )
        
        assert field1 != field2
