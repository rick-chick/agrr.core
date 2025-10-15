"""Gateway interface for loading interaction rules.

This gateway defines the interface for loading interaction rules
from external sources (files, databases, etc.).
"""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.interaction_rule_entity import InteractionRule


class InteractionRuleGateway(ABC):
    """Gateway for loading interaction rules.
    
    Note:
        This gateway should not expose implementation details (like file paths).
        Configuration (file path, database connection, etc.) should be 
        provided at initialization time, not at method call time.
    """
    
    @abstractmethod
    async def get_rules(self) -> List[InteractionRule]:
        """Load interaction rules from configured source.
        
        Returns:
            List of InteractionRule entities
            
        Raises:
            FileError: If source cannot be read or parsed
            
        Note:
            Source configuration is provided at initialization, not here.
        """
        pass

