"""Base class for neighbor operations in local search."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation

class NeighborOperation(ABC):
    """Abstract base class for neighbor operations.
    
    Each concrete operation implements a specific transformation strategy
    to generate neighboring solutions from a current solution.
    
    Design Pattern: Strategy Pattern
    - Each operation encapsulates a specific neighbor generation algorithm
    - Operations can be composed and weighted dynamically
    """
    
    @abstractmethod
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbor solutions from the current solution.
        
        Args:
            solution: Current allocation solution
            context: Context information (candidates, fields, crops, config, etc.)
            
        Returns:
            List of neighbor solutions
        """
        pass
    
    @property
    @abstractmethod
    def operation_name(self) -> str:
        """Return the name of this operation.
        
        Returns:
            Operation name (e.g., "field_swap", "crop_insert")
        """
        pass
    
    @property
    def default_weight(self) -> float:
        """Return the default weight for this operation in sampling.
        
        Returns:
            Default weight (0.0 to 1.0)
        """
        return 1.0

