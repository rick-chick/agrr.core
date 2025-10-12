"""Field replace operation for local search."""

from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.base_neighbor_operation import (
    NeighborOperation,
)
from agrr_core.usecase.services.neighbor_operations.field_move_operation import (
    FieldMoveOperation,
)


class FieldReplaceOperation(NeighborOperation):
    """F3. Field Replace: Replace field with another while keeping crop.
    
    Strategy:
    - Similar to Field Move but tries all fields
    - Delegates to FieldMoveOperation
    """
    
    def __init__(self):
        self._move_operation = FieldMoveOperation()
    
    @property
    def operation_name(self) -> str:
        return "field_replace"
    
    @property
    def default_weight(self) -> float:
        return 0.1
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors by replacing fields."""
        # Field Replace is essentially the same as Field Move
        return self._move_operation.generate_neighbors(solution, context)

