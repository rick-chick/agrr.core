"""Base class for all optimization interactors.

This ensures all optimizers use the same objective function.
"""

from abc import ABC
from typing import List, TypeVar, Generic, Callable, Optional
from agrr_core.entity.value_objects.optimization_objective import (
    OptimizationObjective,
    DEFAULT_OBJECTIVE,
)
from agrr_core.entity.protocols.optimizable import Optimizable


T = TypeVar('T', bound=Optimizable)


class BaseOptimizer(ABC, Generic[T]):
    """Base class for all optimization interactors.
    
    This ensures all optimizers use the same objective function.
    By inheriting from this class, optimizers automatically use
    the unified optimization objective.
    
    ⚠️ CRITICAL: All optimization interactors MUST inherit from this class.
    
    Benefits:
    1. Unified objective function (no manual calculation)
    2. Automatic updates when objective changes
    3. Consistent API across all optimizers
    4. Type-safe optimization
    
    Usage:
        class MyOptimizer(BaseOptimizer[MyCandidateType]):
            def execute(self, request):
                candidates = self._generate_candidates(request)
                optimal = self.select_best(candidates)
                return optimal
    """
    
    def __init__(self, objective: Optional[OptimizationObjective] = None):
        """Initialize optimizer.
        
        Args:
            objective: Optimization objective (uses DEFAULT_OBJECTIVE if None)
        """
        self.objective = objective or DEFAULT_OBJECTIVE
    
    def select_best(self, candidates: List[T]) -> T:
        """Select best candidate using the unified objective function.
        
        ⚠️ This method MUST be used by all subclasses.
        
        Args:
            candidates: List of candidates implementing Optimizable
            
        Returns:
            Best candidate (maximum profit)
            
        Raises:
            ValueError: If candidates is empty
            
        Example:
            candidates = await self._generate_candidates(request)
            optimal = self.select_best(candidates)
        """
        return self.objective.select_best(
            candidates,
            key_func=lambda c: self.objective.calculate(c.get_metrics())
        )
    
    def calculate_value(self, candidate: T) -> float:
        """Calculate objective value for a candidate.
        
        Args:
            candidate: Candidate implementing Optimizable
            
        Returns:
            Objective value (profit)
        """
        return self.objective.calculate(candidate.get_metrics())
    
    def compare_candidates(self, candidate1: T, candidate2: T) -> int:
        """Compare two candidates.
        
        Args:
            candidate1: First candidate
            candidate2: Second candidate
        
        Returns:
            1 if candidate1 is better, -1 if candidate2 is better, 0 if equal
        """
        value1 = self.calculate_value(candidate1)
        value2 = self.calculate_value(candidate2)
        return self.objective.compare(value1, value2)
    
    def sort_candidates(
        self,
        candidates: List[T],
        reverse: bool = True
    ) -> List[T]:
        """Sort candidates by objective value.
        
        Args:
            candidates: List of candidates to sort
            reverse: If True, best candidates first (default)
            
        Returns:
            Sorted list of candidates
        """
        return sorted(
            candidates,
            key=lambda c: self.calculate_value(c),
            reverse=reverse
        )

