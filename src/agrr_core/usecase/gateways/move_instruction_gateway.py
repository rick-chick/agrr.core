"""Move instruction gateway interface.

Gateway for loading move instructions from external sources.
Used in allocation adjustment use case to load user-specified move instructions.

Note:
    Source configuration (file path, database connection, etc.) is provided
    at initialization time, not at method call time.
"""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.move_instruction_entity import MoveInstruction


class MoveInstructionGateway(ABC):
    """Gateway interface for move instruction operations."""
    
    @abstractmethod
    async def get_all(self) -> List[MoveInstruction]:
        """Get all move instructions from configured source.
        
        Returns:
            List of move instruction entities
            
        Note:
            Source is configured at gateway initialization (file, database, API, etc.)
        """
        pass

