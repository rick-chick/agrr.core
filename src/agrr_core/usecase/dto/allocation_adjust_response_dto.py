"""Allocation adjustment response DTO.

Data Transfer Object for allocation adjustment use case response.

Fields:
- optimized_result: The adjusted and re-optimized allocation result
- applied_moves: List of successfully applied move instructions
- rejected_moves: List of rejected move instructions with reasons
- success: Whether the adjustment was successful
- message: Optional message (error message, warnings, etc.)
"""

from dataclasses import dataclass
from typing import List, Optional, Dict

from agrr_core.entity.entities.multi_field_optimization_result_entity import (
    MultiFieldOptimizationResult,
)
from agrr_core.entity.entities.move_instruction_entity import MoveInstruction


@dataclass(frozen=True)
class AllocationAdjustResponseDTO:
    """Response DTO for allocation adjustment use case."""
    
    optimized_result: MultiFieldOptimizationResult
    applied_moves: List[MoveInstruction]
    rejected_moves: List[Dict[str, str]]  # [{"move": MoveInstruction, "reason": str}]
    success: bool
    message: Optional[str] = None
    
    def __post_init__(self):
        """Validate response DTO."""
        if not self.success and not self.message:
            raise ValueError("message is required when success is False")

