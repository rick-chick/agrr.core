"""Move instruction entity.

Represents a user instruction to move, modify, or remove a crop allocation.

This entity is used in the allocation adjustment use case where users want to
manually adjust existing allocations and re-optimize the overall solution.

Fields:
- allocation_id: ID of the allocation to be moved/modified/removed
- action: Type of action (move, remove)
- to_field_id: Target field ID (for move action)
- to_start_date: Target start date (for move action)
- to_area: Target area in m² (for move action)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class MoveAction(str, Enum):
    """Action type for move instruction."""
    
    MOVE = "move"
    REMOVE = "remove"


@dataclass(frozen=True)
class MoveInstruction:
    """Represents a user instruction to move or remove an allocation."""
    
    allocation_id: str
    action: MoveAction
    to_field_id: Optional[str] = None
    to_start_date: Optional[datetime] = None
    to_area: Optional[float] = None
    
    def __post_init__(self):
        """Validate move instruction invariants."""
        if self.action == MoveAction.MOVE:
            if self.to_field_id is None:
                raise ValueError(f"to_field_id is required for MOVE action")
            if self.to_start_date is None:
                raise ValueError(f"to_start_date is required for MOVE action")
            if self.to_area is not None and self.to_area <= 0:
                raise ValueError(f"to_area must be positive, got {self.to_area}")
        
        elif self.action == MoveAction.REMOVE:
            # For REMOVE action, to_* fields should not be specified
            if any([self.to_field_id, self.to_start_date, self.to_area is not None]):
                raise ValueError(f"to_* fields should not be specified for REMOVE action")

