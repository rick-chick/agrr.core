"""Tests for InteractionRuleGatewayImpl."""

import json
import tempfile
from pathlib import Path

import pytest

from agrr_core.adapter.gateways.interaction_rule_gateway_impl import InteractionRuleGatewayImpl
from agrr_core.framework.repositories.file_repository import FileRepository
from agrr_core.entity.exceptions.file_error import FileError
from agrr_core.entity.value_objects.rule_type import RuleType


class TestInteractionRuleGatewayImpl:
    """Test InteractionRuleGatewayImpl."""
    
    @pytest.mark.asyncio
    async def test_get_rules_from_valid_file(self):
        """Test loading rules from a valid JSON file."""
        rules_data = [
            {
                "rule_id": "rule_001",
                "rule_type": "continuous_cultivation",
                "source_group": "Solanaceae",
                "target_group": "Solanaceae",
                "impact_ratio": 0.7,
                "is_directional": True,
                "description": "Solanaceae continuous cultivation damage"
            },
            {
                "rule_id": "rule_002",
                "rule_type": "beneficial_rotation",
                "source_group": "Fabaceae",
                "target_group": "Poaceae",
                "impact_ratio": 1.1,
                "is_directional": True,
                "description": "Legumes to grains"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rules_data, f, ensure_ascii=False)
        
        try:
            file_repository = FileRepository()
            gateway = InteractionRuleGatewayImpl(file_repository)
            
            rules = await gateway.get_rules(str(temp_file))
            
            assert len(rules) == 2
            assert rules[0].rule_id == "rule_001"
            assert rules[0].rule_type == RuleType.CONTINUOUS_CULTIVATION
            assert rules[0].source_group == "Solanaceae"
            assert rules[0].target_group == "Solanaceae"
            assert rules[0].impact_ratio == 0.7
            assert rules[0].is_directional is True
            
            assert rules[1].rule_id == "rule_002"
            assert rules[1].source_group == "Fabaceae"
            assert rules[1].target_group == "Poaceae"
            
        finally:
            temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_get_rules_with_default_is_directional(self):
        """Test that is_directional defaults to True if not specified."""
        rules_data = [
            {
                "rule_id": "rule_001",
                "rule_type": "continuous_cultivation",
                "source_group": "Solanaceae",
                "target_group": "Solanaceae",
                "impact_ratio": 0.7
                # is_directional not specified
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rules_data, f, ensure_ascii=False)
        
        try:
            file_repository = FileRepository()
            gateway = InteractionRuleGatewayImpl(file_repository)
            
            rules = await gateway.get_rules(str(temp_file))
            
            assert len(rules) == 1
            assert rules[0].is_directional is True  # Default value
            
        finally:
            temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_get_rules_with_missing_field_raises_error(self):
        """Test that missing required field raises FileError."""
        rules_data = [
            {
                "rule_id": "rule_001",
                "rule_type": "continuous_cultivation",
                # Missing source_group
                "target_group": "Solanaceae",
                "impact_ratio": 0.7
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rules_data, f, ensure_ascii=False)
        
        try:
            file_repository = FileRepository()
            gateway = InteractionRuleGatewayImpl(file_repository)
            
            with pytest.raises(FileError, match="Missing required field"):
                await gateway.get_rules(str(temp_file))
                
        finally:
            temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_get_rules_with_invalid_json_raises_error(self):
        """Test that invalid JSON raises FileError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            f.write("{ invalid json }")
        
        try:
            file_repository = FileRepository()
            gateway = InteractionRuleGatewayImpl(file_repository)
            
            with pytest.raises(FileError, match="Invalid JSON format"):
                await gateway.get_rules(str(temp_file))
                
        finally:
            temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_get_rules_with_non_list_json_raises_error(self):
        """Test that non-list JSON raises FileError."""
        rule_data = {
            "rule_id": "rule_001",
            "rule_type": "continuous_cultivation",
            "source_group": "Solanaceae",
            "target_group": "Solanaceae",
            "impact_ratio": 0.7
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rule_data, f, ensure_ascii=False)  # Single object, not list
        
        try:
            file_repository = FileRepository()
            gateway = InteractionRuleGatewayImpl(file_repository)
            
            with pytest.raises(FileError, match="expected list"):
                await gateway.get_rules(str(temp_file))
                
        finally:
            temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_get_rules_with_invalid_impact_ratio_raises_error(self):
        """Test that invalid impact_ratio raises FileError."""
        rules_data = [
            {
                "rule_id": "rule_001",
                "rule_type": "continuous_cultivation",
                "source_group": "Solanaceae",
                "target_group": "Solanaceae",
                "impact_ratio": -0.5  # Negative value
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rules_data, f, ensure_ascii=False)
        
        try:
            file_repository = FileRepository()
            gateway = InteractionRuleGatewayImpl(file_repository)
            
            with pytest.raises(FileError, match="Invalid rule data"):
                await gateway.get_rules(str(temp_file))
                
        finally:
            temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_get_rules_empty_list(self):
        """Test loading an empty rules list."""
        rules_data = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(rules_data, f, ensure_ascii=False)
        
        try:
            file_repository = FileRepository()
            gateway = InteractionRuleGatewayImpl(file_repository)
            
            rules = await gateway.get_rules(str(temp_file))
            
            assert len(rules) == 0
            assert isinstance(rules, list)
            
        finally:
            temp_file.unlink()

