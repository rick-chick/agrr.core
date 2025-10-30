"""Field remove operation for local search."""

from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.base_neighbor_operation import (
    NeighborOperation,
)

class FieldRemoveOperation(NeighborOperation):
    """F5. Field Remove: Remove one allocation.
    
    Strategy:
    - Remove each allocation one at a time
    - Useful for eliminating unprofitable allocations
    """
    
    @property
    def operation_name(self) -> str:
        return "field_remove"
    
    @property
    def default_weight(self) -> float:
        return 0.05
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors by removing allocations."""
        neighbors = []
        
        for i in range(len(solution)):
            neighbor = solution[:i] + solution[i+1:]
            neighbors.append(neighbor)
        
        return neighbors

