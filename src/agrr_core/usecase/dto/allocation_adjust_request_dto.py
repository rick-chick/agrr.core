"""Allocation adjustment request DTO.

Data Transfer Object for allocation adjustment use case request.

Fields:
- current_optimization_id: ID of the current optimization result to adjust
- move_instructions: List of move instructions
- planning_period_start: Start date of the planning period
- planning_period_end: End date of the planning period
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from agrr_core.entity.entities.move_instruction_entity import MoveInstruction


@dataclass(frozen=True)
class AllocationAdjustRequestDTO:
    """Request DTO for allocation adjustment use case."""
    
    current_optimization_id: str
    move_instructions: List[MoveInstruction]
    planning_period_start: datetime
    planning_period_end: datetime
    
    def __post_init__(self):
        """Validate request DTO."""
        # Note: current_optimization_id can be empty string if loading from file
        # The actual ID will be retrieved during execution
        
        if not self.move_instructions:
            raise ValueError("move_instructions cannot be empty")
        
        if self.planning_period_end < self.planning_period_start:
            raise ValueError(
                f"planning_period_end ({self.planning_period_end}) must be after "
                f"planning_period_start ({self.planning_period_start})"
            )

