"""Tests for Crop entity."""

import pytest

from agrr_core.entity.entities.crop_entity import Crop


class TestCrop:
    """Test Crop entity."""

    def test_create_crop_with_minimum_fields(self):
        """Test creating a crop with minimum required fields."""
        crop = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
        )

        assert crop.crop_id == "rice"
        assert crop.name == "Rice"
        assert crop.area_per_unit == 0.25
        assert crop.variety is None

    def test_create_crop_with_variety(self):
        """Test creating a crop with variety information."""
        crop = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
            variety="Koshihikari",
        )

        assert crop.crop_id == "rice"
        assert crop.name == "Rice"
        assert crop.area_per_unit == 0.25
        assert crop.variety == "Koshihikari"

    def test_crop_immutability(self):
        """Test that Crop is immutable (frozen dataclass)."""
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
        )

        with pytest.raises(AttributeError):
            crop.crop_id = "new_id"

        with pytest.raises(AttributeError):
            crop.name = "New Name"

        with pytest.raises(AttributeError):
            crop.area_per_unit = 1.0

    def test_crop_with_zero_area_per_unit(self):
        """Test creating a crop with zero area per unit."""
        crop = Crop(
            crop_id="test",
            name="Test Crop",
            area_per_unit=0.0,
        )

        assert crop.area_per_unit == 0.0

    def test_crop_with_large_area_per_unit(self):
        """Test creating a crop with large area per unit."""
        crop = Crop(
            crop_id="pumpkin",
            name="Pumpkin",
            area_per_unit=5.0,
        )

        assert crop.area_per_unit == 5.0

    def test_crop_equality(self):
        """Test that crops with same values are equal."""
        crop1 = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
            variety="Koshihikari",
        )
        crop2 = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
            variety="Koshihikari",
        )

        assert crop1 == crop2

    def test_crop_inequality(self):
        """Test that crops with different values are not equal."""
        crop1 = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
        )
        crop2 = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.5,
        )

        assert crop1 != crop2



