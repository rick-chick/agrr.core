"""Implementation of InteractionRuleGateway using file repository."""

import json
from typing import List

from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.entity.value_objects.rule_type import RuleType
from agrr_core.adapter.interfaces.file_repository_interface import FileRepositoryInterface
from agrr_core.entity.exceptions.file_error import FileError


class InteractionRuleGatewayImpl(InteractionRuleGateway):
    """Implementation of InteractionRuleGateway using FileRepository."""
    
    def __init__(self, file_repository: FileRepositoryInterface):
        """Initialize with file repository.
        
        Args:
            file_repository: Repository for file operations
        """
        self.file_repository = file_repository
    
    async def get_rules(self, file_path: str) -> List[InteractionRule]:
        """Load interaction rules from a JSON file.
        
        Args:
            file_path: Path to the interaction rules JSON file
            
        Returns:
            List of InteractionRule entities
            
        Expected JSON format:
        [
            {
                "rule_id": "rule_001",
                "rule_type": "continuous_cultivation",
                "source_group": "Solanaceae",
                "target_group": "Solanaceae",
                "impact_ratio": 0.7,
                "is_directional": true,
                "description": "Solanaceae continuous cultivation damage"
            },
            ...
        ]
        
        Raises:
            FileError: If file cannot be read or JSON is invalid
        """
        try:
            # Read file using repository
            content = await self.file_repository.read(file_path)
            
            # Parse JSON
            data = json.loads(content)
            
            # Validate that data is a list
            if not isinstance(data, list):
                raise FileError(f"Invalid interaction rules file format: expected list, got {type(data)}")
            
            # Deserialize each rule
            rules = []
            for rule_dict in data:
                try:
                    rule = InteractionRule(
                        rule_id=rule_dict["rule_id"],
                        rule_type=RuleType(rule_dict["rule_type"]),
                        source_group=rule_dict["source_group"],
                        target_group=rule_dict["target_group"],
                        impact_ratio=rule_dict["impact_ratio"],
                        is_directional=rule_dict.get("is_directional", True),
                        description=rule_dict.get("description")
                    )
                    rules.append(rule)
                except KeyError as e:
                    raise FileError(f"Missing required field in rule: {e}")
                except ValueError as e:
                    raise FileError(f"Invalid rule data: {e}")
            
            return rules
            
        except json.JSONDecodeError as e:
            raise FileError(f"Invalid JSON format: {e}")
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"Failed to load interaction rules: {e}")

