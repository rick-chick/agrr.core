"""Interaction rule repository interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.interaction_rule_entity import InteractionRule


class InteractionRuleRepositoryInterface(ABC):
    """Abstract interface for interaction rule repository.
    
    Implementations can be:
    - InteractionRuleFileRepository: Load from JSON files
    - InteractionRuleSQLRepository: Load from SQL database
    - InteractionRuleMemoryRepository: Load from in-memory storage
    """
    
    @abstractmethod
    async def get_rules(self) -> List[InteractionRule]:
        """Get interaction rules from configured source.
        
        Returns:
            List of InteractionRule entities
            
        Note:
            Source configuration (file path, connection string, etc.)
            is injected at repository initialization, not passed here.
        """
        pass

