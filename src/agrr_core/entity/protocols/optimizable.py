"""Protocol for optimizable entities."""

from typing import Protocol
from agrr_core.entity.value_objects.optimization_objective import OptimizationMetrics


class Optimizable(Protocol):
    """Protocol for entities that can be optimized.
    
    All optimization candidates MUST implement this protocol.
    This ensures that optimization interactors can only work with
    entities that provide objective metrics.
    
    Usage:
        @dataclass
        class CandidateDTO:
            cost: float
            revenue: Optional[float] = None
            
            def get_metrics(self) -> OptimizationMetrics:
                return OptimizationMetrics(cost=self.cost, revenue=self.revenue)
    """
    
    def get_metrics(self) -> OptimizationMetrics:
        """Get optimization metrics for this entity.
        
        Returns:
            OptimizationMetrics containing cost and optional revenue
        """
        ...

