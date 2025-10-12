"""Tests for InteractionRule entity."""

import pytest

from agrr_core.entity.entities.interaction_rule_entity import InteractionRule


class TestInteractionRuleCreation:
    """Test InteractionRule entity creation."""
    
    def test_create_directed_interaction_rule(self):
        """Test creating a directed interaction rule."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="continuous_cultivation",
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True,
            description="Solanaceae continuous cultivation damage"
        )
        
        assert rule.rule_id == "rule_001"
        assert rule.rule_type == "continuous_cultivation"
        assert rule.source_group == "Solanaceae"
        assert rule.target_group == "Solanaceae"
        assert rule.impact_ratio == 0.7
        assert rule.is_directional is True
        assert rule.description == "Solanaceae continuous cultivation damage"
    
    def test_create_undirected_interaction_rule(self):
        """Test creating an undirected interaction rule."""
        rule = InteractionRule(
            rule_id="rule_002",
            rule_type="companion_planting",
            source_group="Solanaceae",
            target_group="Lamiaceae",
            impact_ratio=1.15,
            is_directional=False,
            description="Tomato and basil companion planting"
        )
        
        assert rule.is_directional is False
        assert rule.impact_ratio == 1.15
    
    def test_create_field_crop_interaction_rule(self):
        """Test creating a field-crop interaction rule."""
        rule = InteractionRule(
            rule_id="rule_003",
            rule_type="soil_compatibility",
            source_group="field_001",
            target_group="Solanaceae",
            impact_ratio=1.2,
            is_directional=True
        )
        
        assert rule.source_group == "field_001"
        assert rule.target_group == "Solanaceae"
        assert rule.description is None  # Optional field
    
    def test_create_field_group_crop_group_interaction_rule(self):
        """Test creating a field group - crop group interaction rule."""
        rule = InteractionRule(
            rule_id="rule_004",
            rule_type="soil_compatibility",
            source_group="acidic_soil",
            target_group="Brassicaceae",
            impact_ratio=0.8,
            is_directional=True,
            description="Acidic soil reduces Brassicaceae revenue"
        )
        
        assert rule.source_group == "acidic_soil"
        assert rule.target_group == "Brassicaceae"
        assert rule.impact_ratio == 0.8


class TestInteractionRuleValidation:
    """Test InteractionRule validation."""
    
    def test_negative_impact_ratio_raises_error(self):
        """Test that negative impact ratio raises ValueError."""
        with pytest.raises(ValueError, match="impact_ratio must be non-negative"):
            InteractionRule(
                rule_id="rule_001",
                rule_type="continuous_cultivation",
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=-0.5,
                is_directional=True
            )
    
    def test_empty_source_group_raises_error(self):
        """Test that empty source_group raises ValueError."""
        with pytest.raises(ValueError, match="source_group must not be empty"):
            InteractionRule(
                rule_id="rule_001",
                rule_type="continuous_cultivation",
                source_group="",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True
            )
    
    def test_empty_target_group_raises_error(self):
        """Test that empty target_group raises ValueError."""
        with pytest.raises(ValueError, match="target_group must not be empty"):
            InteractionRule(
                rule_id="rule_001",
                rule_type="continuous_cultivation",
                source_group="Solanaceae",
                target_group="",
                impact_ratio=0.7,
                is_directional=True
            )
    
    def test_empty_rule_id_raises_error(self):
        """Test that empty rule_id raises ValueError."""
        with pytest.raises(ValueError, match="rule_id must not be empty"):
            InteractionRule(
                rule_id="",
                rule_type="continuous_cultivation",
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True
            )
    
    def test_empty_rule_type_raises_error(self):
        """Test that empty rule_type raises ValueError."""
        with pytest.raises(ValueError, match="rule_type must not be empty"):
            InteractionRule(
                rule_id="rule_001",
                rule_type="",
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True
            )
    
    def test_zero_impact_ratio_is_valid(self):
        """Test that zero impact ratio is valid (cultivation not possible)."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="continuous_cultivation",
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.0,
            is_directional=True
        )
        
        assert rule.impact_ratio == 0.0


class TestInteractionRuleMatches:
    """Test InteractionRule.matches() method."""
    
    def test_directed_rule_matches_forward(self):
        """Test that directed rule matches in forward direction."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="continuous_cultivation",
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True
        )
        
        assert rule.matches("Solanaceae", "Solanaceae")
    
    def test_directed_rule_does_not_match_backward(self):
        """Test that directed rule does not match in backward direction."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="beneficial_rotation",
            source_group="Fabaceae",
            target_group="Poaceae",
            impact_ratio=1.1,
            is_directional=True
        )
        
        # Forward direction should match
        assert rule.matches("Fabaceae", "Poaceae")
        
        # Backward direction should not match
        assert not rule.matches("Poaceae", "Fabaceae")
    
    def test_undirected_rule_matches_both_directions(self):
        """Test that undirected rule matches in both directions."""
        rule = InteractionRule(
            rule_id="rule_002",
            rule_type="companion_planting",
            source_group="Solanaceae",
            target_group="Lamiaceae",
            impact_ratio=1.15,
            is_directional=False
        )
        
        # Forward direction should match
        assert rule.matches("Solanaceae", "Lamiaceae")
        
        # Backward direction should also match
        assert rule.matches("Lamiaceae", "Solanaceae")
    
    def test_rule_does_not_match_different_groups(self):
        """Test that rule does not match different groups."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="continuous_cultivation",
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True
        )
        
        assert not rule.matches("Solanaceae", "Fabaceae")
    
    def test_field_crop_match_rule(self):
        """Test field-crop matching rule."""
        rule = InteractionRule(
            rule_id="rule_003",
            rule_type="soil_compatibility",
            source_group="field_001",
            target_group="Solanaceae",
            impact_ratio=1.2,
            is_directional=True
        )
        
        assert rule.matches("field_001", "Solanaceae")
        assert not rule.matches("field_002", "Solanaceae")


class TestInteractionRuleGetImpact:
    """Test InteractionRule.get_impact() method."""
    
    def test_get_impact_returns_impact_ratio_when_matches(self):
        """Test that get_impact returns impact_ratio when rule matches."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="continuous_cultivation",
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True
        )
        
        impact = rule.get_impact("Solanaceae", "Solanaceae")
        assert impact == 0.7
    
    def test_get_impact_returns_one_when_does_not_match(self):
        """Test that get_impact returns 1.0 when rule does not match."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="continuous_cultivation",
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True
        )
        
        impact = rule.get_impact("Solanaceae", "Fabaceae")
        assert impact == 1.0
    
    def test_get_impact_undirected_rule(self):
        """Test get_impact with undirected rule in both directions."""
        rule = InteractionRule(
            rule_id="rule_002",
            rule_type="companion_planting",
            source_group="Solanaceae",
            target_group="Lamiaceae",
            impact_ratio=1.15,
            is_directional=False
        )
        
        # Forward direction
        impact_forward = rule.get_impact("Solanaceae", "Lamiaceae")
        assert impact_forward == 1.15
        
        # Backward direction
        impact_backward = rule.get_impact("Lamiaceae", "Solanaceae")
        assert impact_backward == 1.15
    
    def test_get_impact_field_crop_match(self):
        """Test get_impact with field-crop matching rule."""
        rule = InteractionRule(
            rule_id="rule_003",
            rule_type="soil_compatibility",
            source_group="field_001",
            target_group="Solanaceae",
            impact_ratio=1.2,
            is_directional=True
        )
        
        # Matching field and crop group
        impact = rule.get_impact("field_001", "Solanaceae")
        assert impact == 1.2
        
        # Different field
        impact_no_match = rule.get_impact("field_002", "Solanaceae")
        assert impact_no_match == 1.0


class TestInteractionRuleImmutability:
    """Test that InteractionRule is immutable (frozen)."""
    
    def test_interaction_rule_is_frozen(self):
        """Test that InteractionRule fields cannot be modified."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="continuous_cultivation",
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True
        )
        
        with pytest.raises(AttributeError):
            rule.impact_ratio = 0.8
