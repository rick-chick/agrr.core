"""Optimization objective calculation (Entity Layer).

This module provides the single source of truth for optimization objectives.
All optimization interactors MUST use this class to ensure consistency.

Design Principles:
1. Single Objective - Always maximize profit
2. Immutability - Value objects are immutable
3. Type Safety - Explicit types and validation
4. Testability - Pure functions, easy to test

Usage Example:
    # Candidates implement get_metrics() to provide their metrics
    class MyCandidateDTO:
        cost: float
        revenue: float
        
        def get_metrics(self) -> OptimizationMetrics:
            return OptimizationMetrics(cost=self.cost, revenue=self.revenue)
    
    # Calculate objective (always profit)
    objective = OptimizationObjective()
    candidate = MyCandidateDTO(cost=1000, revenue=2000)
    profit = objective.calculate(candidate.get_metrics())  # Returns 1000
    
    # Select best candidate (always maximize profit)
    best = objective.select_best(candidates, key_func=lambda c: objective.calculate(c.get_metrics()))
"""

from dataclasses import dataclass
from typing import Optional, List, Callable, TypeVar


@dataclass(frozen=True)
class OptimizationMetrics:
    """Immutable optimization metrics containing raw calculation parameters.
    
    This value object holds all necessary parameters for revenue/cost/profit calculations.
    The actual calculations are performed as properties.
    
    Fields for crop allocation:
        area_used: Allocated area (m²)
        revenue_per_area: Revenue per area (yen/m²)
        max_revenue: Maximum revenue constraint (optional)
        
    Fields for growth period:
        growth_days: Number of growth days
        daily_fixed_cost: Daily fixed cost (yen/day)
        
    Fields for yield impact:
        yield_factor: Yield reduction factor due to temperature stress (0-1)
                     1.0 = no impact, 0.0 = total loss
        
    Calculated properties:
        cost: Total cost
        revenue: Total revenue (with yield_factor applied)
        profit: Total profit (revenue - cost, with constraints)
    """
    
    # Crop allocation parameters
    area_used: Optional[float] = None
    revenue_per_area: Optional[float] = None
    max_revenue: Optional[float] = None
    
    # Growth period parameters
    growth_days: Optional[int] = None
    daily_fixed_cost: Optional[float] = None
    
    # Yield impact parameters
    yield_factor: float = 1.0  # Default: no yield impact
    
    @property
    def cost(self) -> float:
        """Calculate total cost.
        
        Returns:
            Total cost (growth_days * daily_fixed_cost)
            
        Raises:
            ValueError: If required parameters are missing
        """
        if self.growth_days is None or self.daily_fixed_cost is None:
            raise ValueError("cost calculation requires growth_days and daily_fixed_cost")
        return self.growth_days * self.daily_fixed_cost
    
    @property
    def revenue(self) -> Optional[float]:
        """Calculate total revenue with yield impact.
        
        Formula: revenue = area_used * revenue_per_area * yield_factor
        
        The yield_factor accounts for temperature stress impacts on actual yield:
        - 1.0 = no yield reduction (full harvest)
        - 0.9 = 10% yield loss due to stress
        - 0.0 = complete crop failure
        
        Returns:
            Total revenue (area_used * revenue_per_area * yield_factor) or None
            Capped at max_revenue if specified
        """
        if self.area_used is None or self.revenue_per_area is None:
            return None
        
        # Calculate base revenue
        revenue = self.area_used * self.revenue_per_area
        
        # Apply yield factor (temperature stress impact)
        revenue = revenue * self.yield_factor
        
        # Apply max_revenue constraint
        if self.max_revenue is not None and revenue > self.max_revenue:
            return self.max_revenue
        
        return revenue
    
    @property
    def profit(self) -> float:
        """Calculate profit with constraints.
        
        Cases:
        1. Revenue known: profit = revenue - cost
        2. Revenue unknown: profit = -cost (cost minimization)
        3. Max revenue constraint: revenue is capped, affecting profit
        
        Returns:
            Profit value (to be maximized)
        """
        if self.revenue is None:
            return -self.cost
        
        # Revenue is already capped by max_revenue constraint in revenue property
        profit = self.revenue - self.cost
        
        return profit


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

