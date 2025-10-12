"""Gateway interface for loading interaction rules.

This gateway defines the interface for loading interaction rules
from external sources (files, databases, etc.).
"""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.interaction_rule_entity import InteractionRule


class InteractionRuleGateway(ABC):
    """Gateway for loading interaction rules."""
    
    @abstractmethod
    async def get_rules(self, file_path: str) -> List[InteractionRule]:
        """Load interaction rules from a file.
        
        Args:
            file_path: Path to the interaction rules JSON file
            
        Returns:
            List of InteractionRule entities
            
        Raises:
            FileError: If file cannot be read or parsed
        """
        pass

