"""Move instruction entity.

Represents a user instruction to move, modify, remove, or add a crop allocation.

This entity is used in the allocation adjustment use case where users want to
manually adjust existing allocations and re-optimize the overall solution.

Fields:
- allocation_id: ID of the allocation to be moved/modified/removed (ignored for ADD action)
- action: Type of action (move, remove, add)
- to_field_id: Target field ID (for move/add action)
- to_start_date: Target start date (for move/add action)
- to_area: Target area in m² (for move/add action)
- crop_id: Crop ID (for add action only)
- variety: Crop variety (for add action only, optional)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class MoveAction(str, Enum):
    """Action type for move instruction."""
    
    MOVE = "move"
    REMOVE = "remove"
    ADD = "add"  # Add new crop allocation

@dataclass(frozen=True)
class MoveInstruction:
    """Represents a user instruction to move, remove, or add an allocation."""
    
    allocation_id: str  # Ignored for ADD action (auto-generated)
    action: MoveAction
    to_field_id: Optional[str] = None
    to_start_date: Optional[datetime] = None
    to_area: Optional[float] = None
    crop_id: Optional[str] = None  # Required for ADD action
    variety: Optional[str] = None  # Optional for ADD action
    
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
        
        elif self.action == MoveAction.ADD:
            # For ADD action, validate required fields
            if self.to_field_id is None:
                raise ValueError(f"to_field_id is required for ADD action")
            if self.to_start_date is None:
                raise ValueError(f"to_start_date is required for ADD action")
            if self.to_area is None or self.to_area <= 0:
                raise ValueError(f"to_area must be positive for ADD action, got {self.to_area}")
            if self.crop_id is None:
                raise ValueError(f"crop_id is required for ADD action")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "allocation_id": self.allocation_id,
            "action": self.action.value,
            "to_field_id": self.to_field_id,
            "to_start_date": self.to_start_date.isoformat() if self.to_start_date else None,
            "to_area": self.to_area,
            "crop_id": self.crop_id,
            "variety": self.variety
        }

