"""Implementation of InteractionRuleGateway using file repository."""

import json
from typing import List

from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.entity.value_objects.rule_type import RuleType
from agrr_core.adapter.interfaces.file_repository_interface import FileRepositoryInterface
from agrr_core.entity.exceptions.file_error import FileError


class InteractionRuleGatewayImpl(InteractionRuleGateway):
    """Implementation of InteractionRuleGateway using repository abstraction.
    
    This gateway depends on InteractionRuleRepositoryInterface abstraction,
    not specific implementations (file, SQL, memory, etc.).
    """
    
    def __init__(self, interaction_rule_repository):
        """Initialize with interaction rule repository abstraction.
        
        Args:
            interaction_rule_repository: Repository abstraction for interaction rules
                (InteractionRuleRepositoryInterface - file, SQL, memory, etc.)
        """
        self.interaction_rule_repository = interaction_rule_repository
    
    async def get_rules(self) -> List[InteractionRule]:
        """Load interaction rules from configured repository.
        
        Returns:
            List of InteractionRule entities
            
        Raises:
            ValueError: If repository was not configured at initialization
        """
        if not self.interaction_rule_repository:
            raise ValueError("InteractionRuleRepository not provided. Cannot load rules.")
        
        return await self.interaction_rule_repository.get_rules()

