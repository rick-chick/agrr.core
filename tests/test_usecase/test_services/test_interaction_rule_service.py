"""Tests for InteractionRuleService."""

import pytest

from agrr_core.usecase.services.interaction_rule_service import InteractionRuleService
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.value_objects.rule_type import RuleType


class TestGetContinuousCultivationImpact:
    """Test get_continuous_cultivation_impact method."""
    
    def test_no_previous_crop_returns_one(self):
        """Test that no previous crop returns 1.0 (no impact)."""
        rules = []
        service = InteractionRuleService(rules)
        
        current_crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        impact = service.get_continuous_cultivation_impact(current_crop, None)
        
        assert impact == 1.0
    
    def test_no_groups_returns_one(self):
        """Test that crops without groups return 1.0."""
        rules = []
        service = InteractionRuleService(rules)
        
        current_crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5
            # No groups
        )
        
        previous_crop = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25
            # No groups
        )
        
        impact = service.get_continuous_cultivation_impact(current_crop, previous_crop)
        
        assert impact == 1.0
    
    def test_different_family_no_rule_returns_one(self):
        """Test that different families with no matching rule return 1.0."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type=RuleType.CONTINUOUS_CULTIVATION,
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True
            )
        ]
        service = InteractionRuleService(rules)
        
        current_crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        previous_crop = Crop(
            crop_id="soybean",
            name="Soybean",
            area_per_unit=0.15,
            groups=["Fabaceae"]
        )
        
        impact = service.get_continuous_cultivation_impact(current_crop, previous_crop)
        
        assert impact == 1.0
    
    def test_same_family_continuous_cultivation_applies_penalty(self):
        """Test that same family continuous cultivation applies penalty."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type=RuleType.CONTINUOUS_CULTIVATION,
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True,
                description="Solanaceae continuous cultivation damage"
            )
        ]
        service = InteractionRuleService(rules)
        
        current_crop = Crop(
            crop_id="eggplant",
            name="Eggplant",
            area_per_unit=0.4,
            groups=["Solanaceae"]
        )
        
        previous_crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        impact = service.get_continuous_cultivation_impact(current_crop, previous_crop)
        
        assert impact == 0.7
    
    def test_multiple_groups_finds_matching_rule(self):
        """Test that crops with multiple groups find matching rule."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type=RuleType.CONTINUOUS_CULTIVATION,
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True
            )
        ]
        service = InteractionRuleService(rules)
        
        current_crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae", "fruiting_vegetables", "warm_season"]
        )
        
        previous_crop = Crop(
            crop_id="pepper",
            name="Pepper",
            area_per_unit=0.3,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        impact = service.get_continuous_cultivation_impact(current_crop, previous_crop)
        
        assert impact == 0.7
    
    def test_non_continuous_cultivation_rules_are_ignored(self):
        """Test that non-continuous_cultivation rules are ignored."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type=RuleType.BENEFICIAL_ROTATION,  # Different rule type
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.5,  # Should not be applied
                is_directional=True
            )
        ]
        service = InteractionRuleService(rules)
        
        current_crop = Crop(
            crop_id="eggplant",
            name="Eggplant",
            area_per_unit=0.4,
            groups=["Solanaceae"]
        )
        
        previous_crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        impact = service.get_continuous_cultivation_impact(current_crop, previous_crop)
        
        # No continuous_cultivation rule, so impact should be 1.0
        assert impact == 1.0
    
    def test_multiple_matching_rules_multiply(self):
        """Test that multiple matching rules multiply their impacts."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type=RuleType.CONTINUOUS_CULTIVATION,
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.8,
                is_directional=True
            ),
            InteractionRule(
                rule_id="rule_002",
                rule_type=RuleType.CONTINUOUS_CULTIVATION,
                source_group="fruiting_vegetables",
                target_group="fruiting_vegetables",
                impact_ratio=0.9,
                is_directional=True
            )
        ]
        service = InteractionRuleService(rules)
        
        current_crop = Crop(
            crop_id="eggplant",
            name="Eggplant",
            area_per_unit=0.4,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        previous_crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        impact = service.get_continuous_cultivation_impact(current_crop, previous_crop)
        
        # Both rules apply: 0.8 * 0.9 = 0.72
        assert impact == pytest.approx(0.72, rel=0.001)


class TestGetFieldCropImpact:
    """Test get_field_crop_impact method."""
    
    def test_no_field_groups_returns_one(self):
        """Test that no field groups returns 1.0."""
        rules = []
        service = InteractionRuleService(rules)
        
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        impact = service.get_field_crop_impact(None, crop)
        
        assert impact == 1.0
    
    def test_no_crop_groups_returns_one(self):
        """Test that crop without groups returns 1.0."""
        rules = []
        service = InteractionRuleService(rules)
        
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5
            # No groups
        )
        
        impact = service.get_field_crop_impact(["acidic_soil"], crop)
        
        assert impact == 1.0
    
    def test_matching_soil_compatibility_applies_bonus(self):
        """Test that matching soil compatibility applies bonus."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type=RuleType.SOIL_COMPATIBILITY,
                source_group="acidic_soil",
                target_group="Solanaceae",
                impact_ratio=1.2,
                is_directional=True
            )
        ]
        service = InteractionRuleService(rules)
        
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae"]
        )
        
        impact = service.get_field_crop_impact(["acidic_soil"], crop)
        
        assert impact == 1.2
    
    def test_matching_soil_compatibility_applies_penalty(self):
        """Test that poor soil compatibility applies penalty."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type=RuleType.SOIL_COMPATIBILITY,
                source_group="acidic_soil",
                target_group="Brassicaceae",
                impact_ratio=0.8,
                is_directional=True,
                description="Acidic soil not ideal for Brassicaceae"
            )
        ]
        service = InteractionRuleService(rules)
        
        crop = Crop(
            crop_id="cabbage",
            name="Cabbage",
            area_per_unit=0.3,
            groups=["Brassicaceae"]
        )
        
        impact = service.get_field_crop_impact(["acidic_soil"], crop)
        
        assert impact == 0.8
    
    def test_multiple_field_groups_and_crop_groups(self):
        """Test with multiple field groups and crop groups."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type=RuleType.SOIL_COMPATIBILITY,
                source_group="acidic_soil",
                target_group="Solanaceae",
                impact_ratio=1.1,
                is_directional=True
            ),
            InteractionRule(
                rule_id="rule_002",
                rule_type=RuleType.CLIMATE_COMPATIBILITY,
                source_group="warm_region",
                target_group="warm_season",
                impact_ratio=1.15,
                is_directional=True
            )
        ]
        service = InteractionRuleService(rules)
        
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae", "warm_season"]
        )
        
        impact = service.get_field_crop_impact(["acidic_soil", "warm_region"], crop)
        
        # Both rules apply: 1.1 * 1.15 = 1.265
        assert impact == pytest.approx(1.265, rel=0.001)

