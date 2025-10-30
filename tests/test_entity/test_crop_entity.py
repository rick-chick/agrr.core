"""Tests for Crop entity."""

import pytest

from agrr_core.entity.entities.crop_entity import Crop

class TestCropCreation:
    """Test Crop entity creation."""
    
    def test_create_crop_minimal(self):
        """Test creating a crop with minimal required fields."""
        crop = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25
        )
        
        assert crop.crop_id == "rice"
        assert crop.name == "Rice"
        assert crop.area_per_unit == 0.25
        assert crop.variety is None
        assert crop.revenue_per_area is None
        assert crop.max_revenue is None
        assert crop.groups is None
    
    def test_create_crop_with_variety(self):
        """Test creating a crop with variety."""
        crop = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
            variety="Koshihikari"
        )
        
        assert crop.variety == "Koshihikari"
    
    def test_create_crop_with_revenue(self):
        """Test creating a crop with revenue information."""
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            revenue_per_area=50000.0,
            max_revenue=1000000.0
        )
        
        assert crop.revenue_per_area == 50000.0
        assert crop.max_revenue == 1000000.0
    
    def test_create_crop_with_single_group(self):
        """Test creating a crop with a single group."""
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        assert crop.groups == ["Solanaceae"]
        assert len(crop.groups) == 1
    
    def test_create_crop_with_multiple_groups(self):
        """Test creating a crop with multiple groups."""
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae", "fruiting_vegetables", "warm_season"]
        )
        
        assert crop.groups == ["Solanaceae", "fruiting_vegetables", "warm_season"]
        assert len(crop.groups) == 3
        assert "Solanaceae" in crop.groups
        assert "fruiting_vegetables" in crop.groups
        assert "warm_season" in crop.groups
    
    def test_create_crop_with_all_fields(self):
        """Test creating a crop with all optional fields."""
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            variety="Aiko",
            revenue_per_area=50000.0,
            max_revenue=1000000.0,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        assert crop.crop_id == "tomato"
        assert crop.name == "Tomato"
        assert crop.area_per_unit == 0.5
        assert crop.variety == "Aiko"
        assert crop.revenue_per_area == 50000.0
        assert crop.max_revenue == 1000000.0
        assert crop.groups == ["Solanaceae", "fruiting_vegetables"]
    
    def test_create_crop_with_empty_groups_list(self):
        """Test creating a crop with empty groups list."""
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=[]
        )
        
        assert crop.groups == []
        assert len(crop.groups) == 0

class TestCropGroupExamples:
    """Test various crop group examples."""
    
    def test_solanaceae_family_crops(self):
        """Test Solanaceae (nightshade) family crops."""
        tomato = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        eggplant = Crop(
            crop_id="eggplant",
            name="Eggplant",
            area_per_unit=0.5,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        pepper = Crop(
            crop_id="pepper",
            name="Pepper",
            area_per_unit=0.3,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        # All share Solanaceae group
        assert "Solanaceae" in tomato.groups
        assert "Solanaceae" in eggplant.groups
        assert "Solanaceae" in pepper.groups
    
    def test_brassicaceae_family_crops(self):
        """Test Brassicaceae (crucifer) family crops."""
        cabbage = Crop(
            crop_id="cabbage",
            name="Cabbage",
            area_per_unit=0.4,
            groups=["Brassicaceae", "leafy_vegetables"]
        )
        
        radish = Crop(
            crop_id="radish",
            name="Radish",
            area_per_unit=0.1,
            groups=["Brassicaceae", "root_vegetables"]
        )
        
        # Both share Brassicaceae group
        assert "Brassicaceae" in cabbage.groups
        assert "Brassicaceae" in radish.groups
    
    def test_fabaceae_family_crops(self):
        """Test Fabaceae (legume) family crops."""
        soybean = Crop(
            crop_id="soybean",
            name="Soybean",
            area_per_unit=0.15,
            groups=["Fabaceae", "legumes", "nitrogen_fixing"]
        )
        
        pea = Crop(
            crop_id="pea",
            name="Pea",
            area_per_unit=0.1,
            groups=["Fabaceae", "legumes", "nitrogen_fixing"]
        )
        
        # Both are nitrogen-fixing legumes
        assert "Fabaceae" in soybean.groups
        assert "nitrogen_fixing" in soybean.groups
        assert "Fabaceae" in pea.groups
        assert "nitrogen_fixing" in pea.groups
    
    def test_poaceae_family_crops(self):
        """Test Poaceae (grass) family crops."""
        rice = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
            groups=["Poaceae", "grains", "high_water_need"]
        )
        
        corn = Crop(
            crop_id="corn",
            name="Corn",
            area_per_unit=0.2,
            groups=["Poaceae", "grains"]
        )
        
        # Both are grains
        assert "Poaceae" in rice.groups
        assert "Poaceae" in corn.groups
        assert "grains" in rice.groups
        assert "grains" in corn.groups
    
    def test_functional_groups(self):
        """Test crops with functional group classification."""
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=[
                "Solanaceae",           # Botanical family
                "fruiting_vegetables",  # Functional type
                "warm_season",          # Climate requirement
                "high_water_need",      # Water requirement
                "deep_root"             # Root characteristic
            ]
        )
        
        # Check all group types are present
        assert "Solanaceae" in crop.groups
        assert "fruiting_vegetables" in crop.groups
        assert "warm_season" in crop.groups
        assert "high_water_need" in crop.groups
        assert "deep_root" in crop.groups

class TestCropImmutability:
    """Test that Crop entity is immutable (frozen)."""
    
    def test_crop_is_frozen(self):
        """Test that Crop fields cannot be modified."""
        crop = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25
        )
        
        with pytest.raises(AttributeError):
            crop.name = "Wheat"
    
    def test_crop_groups_list_cannot_be_reassigned(self):
        """Test that groups list cannot be reassigned."""
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        with pytest.raises(AttributeError):
            crop.groups = ["Fabaceae"]

class TestCropEquality:
    """Test Crop entity equality."""
    
    def test_crops_with_same_values_are_equal(self):
        """Test that crops with same values are equal."""
        crop1 = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25
        )
        
        crop2 = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25
        )
        
        assert crop1 == crop2
    
    def test_crops_with_same_values_including_groups_are_equal(self):
        """Test that crops with same values including groups are equal."""
        crop1 = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        crop2 = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        assert crop1 == crop2
    
    def test_crops_with_different_groups_are_not_equal(self):
        """Test that crops with different groups are not equal."""
        crop1 = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        crop2 = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Fabaceae"]
        )
        
        assert crop1 != crop2
    
    def test_crop_with_groups_and_without_groups_are_not_equal(self):
        """Test that crop with groups and without groups are not equal."""
        crop1 = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        crop2 = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5
        )
        
        assert crop1 != crop2
