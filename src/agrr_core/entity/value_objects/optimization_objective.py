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
from typing import Optional, List, Callable, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
    from agrr_core.entity.entities.field_entity import Field
    from agrr_core.entity.entities.crop_entity import Crop
    from agrr_core.entity.entities.interaction_rule_entity import InteractionRule


@dataclass(frozen=True)
class OptimizationMetrics:
    """Immutable optimization metrics containing raw calculation parameters.
    
    This value object holds all necessary parameters for revenue/cost/profit calculations.
    The actual calculations are performed as properties.
    
    Fields for crop allocation:
        area_used: Allocated area (m²)
        revenue_per_area: Revenue per area (yen/m²)
        max_revenue: Market demand limit per crop (optional, yen)
        crop_cumulative_revenue: Cumulative revenue already allocated for this crop
                                across all fields (for max_revenue budget tracking)
        
    Fields for growth period:
        growth_days: Number of growth days
        daily_fixed_cost: Daily fixed cost (yen/day)
        
    Fields for yield impact:
        yield_factor: Yield reduction factor due to temperature stress (0-1)
                     1.0 = no impact, 0.0 = total loss
        
    Calculated properties:
        cost: Total cost
        revenue: Total revenue (with yield_factor, interaction_impact, and market demand limit applied)
        profit: Total profit (revenue - cost)
    """
    
    # Crop allocation parameters
    area_used: Optional[float] = None
    revenue_per_area: Optional[float] = None
    max_revenue: Optional[float] = None
    crop_cumulative_revenue: float = 0.0  # Cumulative revenue for this crop across all fields
    interaction_impact: float = 1.0  # Impact from interaction rules (e.g., continuous cultivation)
    
    # Growth period parameters
    growth_days: Optional[int] = None
    daily_fixed_cost: Optional[float] = None
    
    # Yield impact parameters
    yield_factor: float = 1.0  # Default: no yield impact
    
    @classmethod
    def create_for_allocation(
        cls,
        area_used: float,
        revenue_per_area: Optional[float],
        max_revenue: Optional[float],
        growth_days: int,
        daily_fixed_cost: float,
        crop_id: str,
        crop: 'Crop',
        field: 'Field',
        start_date,
        current_allocations: Optional[List['CropAllocation']] = None,
        field_schedules: Optional[dict] = None,
        interaction_rules: Optional[List['InteractionRule']] = None,
        yield_factor: float = 1.0,
    ) -> 'OptimizationMetrics':
        """Create OptimizationMetrics for allocation with automatic calculations.
        
        This factory method automatically calculates:
        - crop_cumulative_revenue from current_allocations
        - interaction_impact from field_schedules and interaction_rules
        
        This is the RECOMMENDED way to create OptimizationMetrics for allocations.
        
        Args:
            area_used: Allocated area (m²)
            revenue_per_area: Revenue per area (yen/m²)
            max_revenue: Market demand limit for this crop (yen)
            growth_days: Number of growth days
            daily_fixed_cost: Daily fixed cost (yen/day)
            crop_id: Crop identifier (for cumulative revenue lookup)
            crop: Crop entity (for interaction rules)
            field: Field entity (for interaction rules)
            start_date: Start date (for interaction rules)
            current_allocations: Currently selected allocations
            field_schedules: Dict mapping field_id to allocations
            interaction_rules: List of interaction rules
            yield_factor: Yield reduction factor (default: 1.0)
            
        Returns:
            OptimizationMetrics with all calculations performed
        """
        # Calculate cumulative revenue (SINGLE SOURCE OF TRUTH)
        crop_cumulative_revenue = 0.0
        if current_allocations:
            crop_cumulative_revenue = cls.calculate_crop_cumulative_revenue(
                crop_id, current_allocations
            )
        
        # Calculate interaction impact (SINGLE SOURCE OF TRUTH)
        interaction_impact = 1.0
        if field_schedules is not None:
            interaction_impact = cls.calculate_interaction_impact(
                crop, field, start_date, field_schedules, interaction_rules
            )
        
        return cls(
            area_used=area_used,
            revenue_per_area=revenue_per_area,
            max_revenue=max_revenue,
            crop_cumulative_revenue=crop_cumulative_revenue,
            interaction_impact=interaction_impact,
            growth_days=growth_days,
            daily_fixed_cost=daily_fixed_cost,
            yield_factor=yield_factor,
        )
    
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
        """Calculate total revenue with all impacts applied.
        
        Formula: revenue = area_used * revenue_per_area * yield_factor * interaction_impact
        
        Factors applied:
        1. yield_factor: Temperature stress impacts on actual yield
           - 1.0 = no yield reduction (full harvest)
           - 0.9 = 10% yield loss due to stress
           - 0.0 = complete crop failure
        
        2. interaction_impact: Crop interaction effects (e.g., continuous cultivation)
           - 1.0 = no impact
           - 0.75 = 25% reduction (continuous cultivation penalty)
           - 1.1 = 10% increase (beneficial rotation)
        
        3. Market demand budget (max_revenue):
           - max_revenue represents market demand/contract limit for this crop
           - crop_cumulative_revenue tracks how much has already been sold
           - Remaining capacity: max(0, max_revenue - crop_cumulative_revenue)
           - This allocation's revenue is capped by remaining capacity
           - If capacity exhausted, revenue = 0 (planting allowed, but unsellable)
        
        Example:
            Carrot max_revenue = 8000 yen (market can only buy this much)
            Allocation 1: cumulative=0    → revenue=8000, new cumulative=8000
            Allocation 2: cumulative=8000 → revenue=0 (market saturated)
            Allocation 3: cumulative=8000 → revenue=0 (market saturated)
        
        Returns:
            Total revenue (with all impacts applied) or None
        """
        if self.area_used is None or self.revenue_per_area is None:
            return None
        
        # Calculate base revenue
        revenue = self.area_used * self.revenue_per_area
        
        # Apply yield factor (temperature stress impact)
        revenue = revenue * self.yield_factor
        
        # Apply interaction impact (continuous cultivation, rotation, etc.)
        revenue = revenue * self.interaction_impact
        
        # Apply market demand limit (farm-wide cumulative sales)
        if self.max_revenue is not None:
            remaining_capacity = max(0.0, self.max_revenue - self.crop_cumulative_revenue)
            # Cap this allocation's revenue at remaining market capacity
            revenue = min(revenue, remaining_capacity)
        
        return revenue
    
    @property
    def profit(self) -> float:
        """Calculate profit.
        
        Cases:
        1. Revenue known: profit = revenue - cost
        2. Revenue unknown: profit = -cost (cost minimization)
        3. Market demand limit: revenue is capped by remaining capacity
        
        Returns:
            Profit value (to be maximized)
        """
        if self.revenue is None:
            return -self.cost
        
        # Revenue is already capped by market demand limit in revenue property
        profit = self.revenue - self.cost
        
        return profit
    
    @staticmethod
    def calculate_crop_cumulative_revenue(crop_id: str, current_allocations: List['CropAllocation']) -> float:
        """Calculate cumulative revenue for a specific crop from current allocations.
        
        This is the SINGLE SOURCE OF TRUTH for crop revenue aggregation.
        Used for market demand limit tracking across the farm.
        
        Args:
            crop_id: The crop to calculate cumulative revenue for
            current_allocations: List of CropAllocation or any object with:
                  - crop (with crop_id)
                  - expected_revenue (or revenue property)
                  
        Returns:
            Cumulative revenue for this crop across all allocations
            
        Example:
            cumulative = OptimizationMetrics.calculate_crop_cumulative_revenue(
                'Carrot', current_allocations
            )
            # Returns: 8000.0
        """
        cumulative_revenue = 0.0
        
        for item in current_allocations:
            # Check if this allocation is for the target crop
            if item.crop.crop_id == crop_id:
                # Accumulate revenue
                if item.expected_revenue is not None:
                    cumulative_revenue += item.expected_revenue
        
        return cumulative_revenue
    
    @classmethod
    def recalculate_allocations_with_context(
        cls, 
        allocations: List['CropAllocation'],
        field_schedules: Optional[dict] = None,
        interaction_rules: Optional[List['InteractionRule']] = None
    ) -> List['CropAllocation']:
        """Recalculate all allocations with proper context (cumulative revenue, interaction impact, etc.).
        
        This is the SINGLE SOURCE OF TRUTH for recalculating allocations after DP or other operations.
        Uses create_for_allocation() factory to ensure all profit calculations are unified.
        
        Strategy:
        1. Group allocations by crop
        2. Sort by profit rate (descending) for each crop
        3. Recalculate each allocation using create_for_allocation() factory
        4. All calculations (cumulative revenue, interaction impact) handled automatically
        
        Args:
            allocations: List of allocations to recalculate
            field_schedules: Dict mapping field_id to allocations (for interaction rules)
            interaction_rules: List of interaction rules (for continuous cultivation, etc.)
            
        Returns:
            Recalculated allocations with correct revenue/profit
            
        Example:
            # After DP allocation (revenue not considering cumulative context)
            allocations = dp_allocate(...)
            # Recalculate with proper context
            allocations = OptimizationMetrics.recalculate_allocations_with_context(
                allocations, field_schedules, interaction_rules
            )
        """
        import dataclasses
        
        # Sort all allocations by profit rate (descending)
        # This ensures best allocations get revenue budget first
        sorted_allocs = sorted(allocations, key=lambda a: a.profit_rate, reverse=True)
        
        # Recalculate each allocation with cumulative context
        # calculate_crop_cumulative_revenue() automatically tracks per-crop cumulative
        # No need to manually group by crop!
        final_allocations = []
        processed_allocs = []
        
        for alloc in sorted_allocs:
            # Use create_for_allocation() factory - handles all calculations internally
            # Automatically calculates crop_cumulative_revenue for this crop
            metrics = cls.create_for_allocation(
                area_used=alloc.area_used,
                revenue_per_area=alloc.crop.revenue_per_area,
                max_revenue=alloc.crop.max_revenue,
                growth_days=alloc.growth_days,
                daily_fixed_cost=alloc.field.daily_fixed_cost,
                crop_id=alloc.crop.crop_id,
                crop=alloc.crop,
                field=alloc.field,
                start_date=alloc.start_date,
                current_allocations=processed_allocs,
                field_schedules=field_schedules,
                interaction_rules=interaction_rules,
            )
            
            # Extract calculated values
            new_revenue = metrics.revenue if metrics.revenue is not None else 0.0
            new_profit = metrics.profit
            
            # Create new allocation with recalculated revenue/profit
            adjusted_alloc = dataclasses.replace(
                alloc,
                expected_revenue=new_revenue,
                profit=new_profit
            )
            final_allocations.append(adjusted_alloc)
            processed_allocs.append(adjusted_alloc)
        
        return final_allocations
    
    @staticmethod
    def calculate_interaction_impact(
        crop: 'Crop',
        field: 'Field',
        start_date,
        field_schedules: dict,
        interaction_rules: Optional[List['InteractionRule']] = None
    ) -> float:
        """Calculate interaction impact for a crop allocation.
        
        This is the SINGLE SOURCE OF TRUTH for interaction rule application.
        Checks the previous crop in the field and applies relevant interaction rules.
        
        Args:
            crop: The crop being allocated
            field: The field being allocated to
            start_date: Start date of this allocation
            field_schedules: Dict mapping field_id to list of allocations
            interaction_rules: List of interaction rules (optional)
            
        Returns:
            Interaction impact factor (1.0 = no impact, <1.0 = penalty, >1.0 = benefit)
            
        Example:
            impact = OptimizationMetrics.calculate_interaction_impact(
                crop, field, start_date, field_schedules, rules
            )
            # Returns: 0.75 (continuous cultivation penalty)
        """
        if not interaction_rules:
            return 1.0
        
        # Get previous allocation in this field
        field_allocs = field_schedules.get(field.field_id, [])
        if not field_allocs:
            return 1.0  # No previous crop
        
        # Find the allocation that ends just before this one
        previous_alloc = None
        for alloc in field_allocs:
            if alloc.completion_date <= start_date:
                if previous_alloc is None or alloc.completion_date > previous_alloc.completion_date:
                    previous_alloc = alloc
        
        if not previous_alloc:
            return 1.0  # No previous crop before this date
        
        previous_crop = previous_alloc.crop
        
        # No previous crop, no impact
        if previous_crop is None:
            return 1.0
        
        # If either crop has no groups, no impact
        if not crop.groups or not previous_crop.groups:
            return 1.0
        
        # Import RuleType here to avoid circular dependency
        from agrr_core.entity.value_objects.rule_type import RuleType
        
        # Find all applicable continuous_cultivation rules
        combined_impact = 1.0
        
        for prev_group in previous_crop.groups:
            for curr_group in crop.groups:
                for rule in interaction_rules:
                    # Only check continuous_cultivation rules
                    if rule.rule_type != RuleType.CONTINUOUS_CULTIVATION:
                        continue
                    
                    # Get impact for this group combination
                    impact = rule.get_impact(prev_group, curr_group)
                    
                    # If impact is not 1.0, apply it (multiply)
                    if impact != 1.0:
                        combined_impact *= impact
        
        return combined_impact


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

