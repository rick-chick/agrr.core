"""Interaction rule file gateway implementation.

This gateway directly implements InteractionRuleGateway interface for file-based interaction rule access.
"""

import json
from typing import List

from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.entity.value_objects.rule_type import RuleType
from agrr_core.adapter.interfaces.file_repository_interface import FileRepositoryInterface
from agrr_core.entity.exceptions.file_error import FileError
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway


class InteractionRuleFileGateway(InteractionRuleGateway):
    """File-based implementation of InteractionRuleGateway.
    
    Directly implements InteractionRuleGateway interface without intermediate layers.
    Reads interaction rules from JSON files.
    File path is configured at initialization.
    """
    
    def __init__(self, file_repository: FileRepositoryInterface, file_path: str):
        """Initialize interaction rule file gateway.
        
        Args:
            file_repository: File repository for file I/O operations (Framework layer)
            file_path: File path to interaction rules JSON file
        """
        self.file_repository = file_repository
        self.file_path = file_path
    
    async def get_rules(self) -> List[InteractionRule]:
        """Get interaction rules from configured file.
        
        Returns:
            List of InteractionRule entities
            
        Raises:
            FileError: If file cannot be read or JSON is invalid
        """
        try:
            # Read file using repository
            content = await self.file_repository.read(self.file_path)
            
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

