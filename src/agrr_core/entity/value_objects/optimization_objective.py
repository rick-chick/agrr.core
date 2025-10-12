"""Optimization objective calculation (Entity Layer).

This module provides the single source of truth for optimization objectives.
All optimization interactors MUST use this class to ensure consistency.

Design Principles:
1. Single Objective - Always maximize profit
2. Immutability - Value objects are immutable
3. Type Safety - Explicit types and validation
4. Testability - Pure functions, easy to test

Usage Example:
    # Create metrics
    metrics = OptimizationMetrics.from_cost_and_revenue(cost=1000, revenue=2000)
    
    # Calculate objective (always profit)
    objective = OptimizationObjective()
    profit = objective.calculate(metrics)  # Returns 1000
    
    # Select best candidate (always maximize profit)
    best = objective.select_best(candidates, key_func=lambda c: c.get_metrics())
"""

from dataclasses import dataclass
from typing import Optional, List, Callable, TypeVar


@dataclass(frozen=True)
class OptimizationMetrics:
    """Immutable optimization metrics.
    
    This value object encapsulates cost and optional revenue.
    Profit is calculated automatically.
    
    Fields:
        cost: Total cost (required)
        revenue: Total revenue (optional)
    """
    
    cost: float
    revenue: Optional[float] = None
    
    def __post_init__(self):
        """Validate metrics."""
        if self.cost < 0:
            raise ValueError(f"cost must be non-negative, got {self.cost}")
        
        if self.revenue is not None and self.revenue < 0:
            raise ValueError(f"revenue must be non-negative, got {self.revenue}")
    
    @property
    def profit(self) -> float:
        """Calculate profit.
        
        Cases:
        1. Revenue known: profit = revenue - cost
        2. Revenue unknown: profit = -cost (equivalent to cost minimization)
        
        Returns:
            Profit value (to be maximized)
        """
        if self.revenue is None:
            return -self.cost
        return self.revenue - self.cost
    
    @staticmethod
    def from_cost_only(cost: float) -> "OptimizationMetrics":
        """Create metrics with cost only.
        
        Args:
            cost: Total cost
            
        Returns:
            OptimizationMetrics with only cost (profit = -cost)
        """
        return OptimizationMetrics(cost=cost)
    
    @staticmethod
    def from_cost_and_revenue(cost: float, revenue: float) -> "OptimizationMetrics":
        """Create metrics with cost and revenue.
        
        Args:
            cost: Total cost
            revenue: Total revenue
            
        Returns:
            OptimizationMetrics with cost and revenue (profit auto-calculated)
        """
        return OptimizationMetrics(cost=cost, revenue=revenue)


class OptimizationObjective:
    """Single objective: Always maximize profit.
    
    This class is the SINGLE SOURCE OF TRUTH for all optimization objectives.
    
    ⚠️ CRITICAL: When modifying the objective function:
    1. Update calculate() method
    2. Update all tests in test_optimization_objective.py
    3. Update documentation
    4. All optimizers will automatically use the new objective
    
    Design: Always maximize profit = revenue - cost (or -cost if revenue unknown)
    """
    
    def calculate(self, metrics: OptimizationMetrics) -> float:
        """Calculate objective value (profit).
        
        ⚠️ THIS IS THE CORE FUNCTION THAT DEFINES WHAT WE OPTIMIZE.
        ALL changes to optimization logic MUST be made here.
        
        Current: profit = revenue - cost (or -cost if revenue is None)
        Future:  profit = revenue - cost - tax + subsidy
        
        Args:
            metrics: Optimization metrics
            
        Returns:
            Profit value (to be maximized)
        """
        return metrics.profit
    
    T = TypeVar('T')
    
    def select_best(
        self, 
        candidates: List[T], 
        key_func: Callable[[T], float]
    ) -> T:
        """Select best candidate (maximum profit).
        
        Args:
            candidates: List of candidates
            key_func: Function to extract profit from candidate
            
        Returns:
            Best candidate (maximum profit)
            
        Raises:
            ValueError: If candidates is empty
            
        Example:
            objective = OptimizationObjective()
            best = objective.select_best(
                candidates,
                key_func=lambda c: objective.calculate(c.get_metrics())
            )
        """
        if not candidates:
            raise ValueError("Cannot select best from empty candidates")
        
        return max(candidates, key=key_func)
    
    def compare(self, value1: float, value2: float) -> int:
        """Compare two objective values.
        
        Args:
            value1: First objective value
            value2: Second objective value
            
        Returns:
            1 if value1 is better, -1 if value2 is better, 0 if equal
        """
        if value1 > value2:
            return 1
        elif value1 < value2:
            return -1
        return 0
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return "OptimizationObjective(maximize_profit)"


# Singleton instance for convenience
DEFAULT_OBJECTIVE = OptimizationObjective()

