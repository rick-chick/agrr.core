"""Integration tests for InteractionRule JSON file loading.

This test suite verifies that InteractionRule entities can be correctly
serialized to and deserialized from JSON files.
"""

import json
import tempfile
from pathlib import Path

import pytest

from agrr_core.entity.entities.interaction_rule_entity import InteractionRule


def serialize_rule(rule: InteractionRule) -> dict:
    """Helper function to serialize InteractionRule to dict."""
    return {
        "rule_id": rule.rule_id,
        "rule_type": rule.rule_type,
        "source_group": rule.source_group,
        "target_group": rule.target_group,
        "impact_ratio": rule.impact_ratio,
        "is_directional": rule.is_directional,
        "description": rule.description
    }


def deserialize_rule(rule_dict: dict) -> InteractionRule:
    """Helper function to deserialize InteractionRule from dict."""
    return InteractionRule(
        rule_id=rule_dict["rule_id"],
        rule_type=rule_dict["rule_type"],
        source_group=rule_dict["source_group"],
        target_group=rule_dict["target_group"],
        impact_ratio=rule_dict["impact_ratio"],
        is_directional=rule_dict["is_directional"],
        description=rule_dict.get("description")
    )


class TestInteractionRuleJSONSerialization:
    """Test JSON serialization and deserialization of InteractionRule."""
    
    def test_serialize_directed_rule_to_json(self):
        """Test serializing a directed InteractionRule to JSON."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="continuous_cultivation",
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True,
            description="Solanaceae continuous cultivation damage"
        )
        
        # Serialize
        rule_dict = serialize_rule(rule)
        json_str = json.dumps(rule_dict, ensure_ascii=False, indent=2)
        
        # Verify
        parsed = json.loads(json_str)
        assert parsed["rule_id"] == "rule_001"
        assert parsed["source_group"] == "Solanaceae"
        assert parsed["impact_ratio"] == 0.7
    
    def test_deserialize_directed_rule_from_json(self):
        """Test deserializing a directed InteractionRule from JSON."""
        json_data = {
            "rule_id": "rule_001",
            "rule_type": "continuous_cultivation",
            "source_group": "Solanaceae",
            "target_group": "Solanaceae",
            "impact_ratio": 0.7,
            "is_directional": True,
            "description": "Solanaceae continuous cultivation damage"
        }
        
        # Deserialize
        rule = deserialize_rule(json_data)
        
        # Verify
        assert rule.rule_id == "rule_001"
        assert rule.rule_type == "continuous_cultivation"
        assert rule.source_group == "Solanaceae"
        assert rule.impact_ratio == 0.7
        assert rule.is_directional is True
    
    def test_roundtrip_serialization(self):
        """Test roundtrip serialization."""
        original = InteractionRule(
            rule_id="rule_002",
            rule_type="companion_planting",
            source_group="Solanaceae",
            target_group="Lamiaceae",
            impact_ratio=1.15,
            is_directional=False
        )
        
        # Serialize and deserialize
        serialized = serialize_rule(original)
        deserialized = deserialize_rule(serialized)
        
        # Verify
        assert deserialized.rule_id == original.rule_id
        assert deserialized.source_group == original.source_group
        assert deserialized.target_group == original.target_group
        assert deserialized.impact_ratio == original.impact_ratio
        assert deserialized.is_directional == original.is_directional


class TestInteractionRuleFileOperations:
    """Test file I/O operations for InteractionRule."""
    
    def test_save_and_load_single_rule(self):
        """Test saving and loading a single rule from JSON file."""
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type="continuous_cultivation",
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True,
            description="Solanaceae continuous cultivation damage"
        )
        
        # Save to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(serialize_rule(rule), f, ensure_ascii=False, indent=2)
        
        try:
            # Load from file
            with open(temp_file, 'r', encoding='utf-8') as f:
                loaded_dict = json.load(f)
            
            loaded_rule = deserialize_rule(loaded_dict)
            
            # Verify
            assert loaded_rule.rule_id == rule.rule_id
            assert loaded_rule.source_group == rule.source_group
            assert loaded_rule.impact_ratio == rule.impact_ratio
            
        finally:
            temp_file.unlink()
    
    def test_save_and_load_multiple_rules(self):
        """Test saving and loading multiple rules from JSON file."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type="continuous_cultivation",
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True
            ),
            InteractionRule(
                rule_id="rule_002",
                rule_type="beneficial_rotation",
                source_group="Fabaceae",
                target_group="Poaceae",
                impact_ratio=1.1,
                is_directional=True
            ),
            InteractionRule(
                rule_id="rule_003",
                rule_type="soil_compatibility",
                source_group="field_001",
                target_group="Solanaceae",
                impact_ratio=1.2,
                is_directional=True
            )
        ]
        
        # Serialize all rules
        rules_list = [serialize_rule(rule) for rule in rules]
        
        # Save to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rules_list, f, ensure_ascii=False, indent=2)
        
        try:
            # Load from file
            with open(temp_file, 'r', encoding='utf-8') as f:
                loaded_list = json.load(f)
            
            loaded_rules = [deserialize_rule(rule_dict) for rule_dict in loaded_list]
            
            # Verify
            assert len(loaded_rules) == 3
            assert loaded_rules[0].rule_id == "rule_001"
            assert loaded_rules[1].rule_id == "rule_002"
            assert loaded_rules[2].rule_id == "rule_003"
            assert loaded_rules[2].source_group == "field_001"
            
        finally:
            temp_file.unlink()


class TestInteractionRuleMatchingWithJSON:
    """Test InteractionRule matching with JSON-loaded rules."""
    
    def test_load_and_apply_continuous_cultivation_rule(self):
        """Test loading a rule from JSON and applying it to groups."""
        rule_data = {
            "rule_id": "rule_001",
            "rule_type": "continuous_cultivation",
            "source_group": "Solanaceae",
            "target_group": "Solanaceae",
            "impact_ratio": 0.7,
            "is_directional": True,
            "description": "Solanaceae continuous cultivation damage"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rule_data, f, ensure_ascii=False)
        
        try:
            # Load rule
            with open(temp_file, 'r', encoding='utf-8') as f:
                loaded_dict = json.load(f)
            
            rule = deserialize_rule(loaded_dict)
            
            # Test matching
            impact = rule.get_impact("Solanaceae", "Solanaceae")
            assert impact == 0.7  # Continuous cultivation penalty applied
            
            # Test non-matching
            impact_no_match = rule.get_impact("Fabaceae", "Solanaceae")
            assert impact_no_match == 1.0  # No penalty
            
        finally:
            temp_file.unlink()
    
    def test_load_and_apply_field_crop_compatibility_rule(self):
        """Test loading a field-crop compatibility rule and applying it."""
        rule_data = {
            "rule_id": "rule_002",
            "rule_type": "soil_compatibility",
            "source_group": "field_001",
            "target_group": "Solanaceae",
            "impact_ratio": 1.2,
            "is_directional": True,
            "description": "Field 001 is well-suited for Solanaceae"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rule_data, f, ensure_ascii=False)
        
        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                loaded_dict = json.load(f)
            
            rule = deserialize_rule(loaded_dict)
            
            # Test matching
            impact = rule.get_impact("field_001", "Solanaceae")
            assert impact == 1.2  # Field is well-suited, 20% bonus
            
            # Test non-matching field
            impact_different_field = rule.get_impact("field_002", "Solanaceae")
            assert impact_different_field == 1.0  # No bonus
            
        finally:
            temp_file.unlink()


class TestRealWorldInteractionRuleScenarios:
    """Test real-world scenarios with interaction rules."""
    
    def test_comprehensive_rule_set_for_optimization(self):
        """Test a comprehensive set of rules that could be used in optimization."""
        rules_json = [
            {
                "rule_id": "cc_001",
                "rule_type": "continuous_cultivation",
                "source_group": "Solanaceae",
                "target_group": "Solanaceae",
                "impact_ratio": 0.7,
                "is_directional": True,
                "description": "Solanaceae continuous cultivation (30% penalty)"
            },
            {
                "rule_id": "cc_002",
                "rule_type": "continuous_cultivation",
                "source_group": "Brassicaceae",
                "target_group": "Brassicaceae",
                "impact_ratio": 0.8,
                "is_directional": True,
                "description": "Brassicaceae continuous cultivation (20% penalty)"
            },
            {
                "rule_id": "rot_001",
                "rule_type": "beneficial_rotation",
                "source_group": "Fabaceae",
                "target_group": "Poaceae",
                "impact_ratio": 1.1,
                "is_directional": True,
                "description": "Legumes to grains (10% bonus)"
            },
            {
                "rule_id": "soil_001",
                "rule_type": "soil_compatibility",
                "source_group": "acidic_soil",
                "target_group": "Brassicaceae",
                "impact_ratio": 0.8,
                "is_directional": True,
                "description": "Acidic soil not ideal for Brassicaceae (20% penalty)"
            }
        ]
        
        # Save to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rules_json, f, ensure_ascii=False, indent=2)
        
        try:
            # Load all rules
            with open(temp_file, 'r', encoding='utf-8') as f:
                loaded_list = json.load(f)
            
            rules = [deserialize_rule(rule_dict) for rule_dict in loaded_list]
            
            # Verify we loaded all rules
            assert len(rules) == 4
            
            # Verify we can find specific rules
            cc_rules = [r for r in rules if r.rule_type == "continuous_cultivation"]
            assert len(cc_rules) == 2
            
            rot_rules = [r for r in rules if r.rule_type == "beneficial_rotation"]
            assert len(rot_rules) == 1
            
            soil_rules = [r for r in rules if r.rule_type == "soil_compatibility"]
            assert len(soil_rules) == 1
            
        finally:
            temp_file.unlink()
