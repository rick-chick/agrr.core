"""Optimal growth period calculation response DTO.

This DTO carries the calculated optimal growth period and comparison of all candidates.

Fields
- crop_name: Human-readable crop name
- variety: Variety/cultivar if specified
- optimal_start_date: Optimal start date (minimum cost)
- completion_date: Date when growth reaches 100%
- growth_days: Number of days from start to completion
- total_cost: Total cost for optimal period
- daily_fixed_cost: Daily fixed cost used in calculation
- field: Field entity used in calculation
- candidates: List of all candidate evaluation results
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.value_objects.optimization_objective import OptimizationMetrics


@dataclass
class CandidateResultDTO:
    """Evaluation result for a single candidate start date.
    
    Implements Optimizable protocol for unified optimization.
    This class holds raw parameters for metric calculation.
    """

    start_date: datetime
    completion_date: Optional[datetime]  # None if 100% not achieved
    growth_days: Optional[int]
    field: Optional[Field] = None  # Field entity for cost calculation
    crop: Optional[Crop] = None  # Crop entity for revenue calculation
    is_optimal: bool = False
    yield_factor: float = 1.0  # Yield impact from temperature stress (default: no impact)

    def get_metrics(self) -> OptimizationMetrics:
        """Get optimization metrics with raw calculation parameters (implements Optimizable protocol).
        
        Returns OptimizationMetrics with all raw data needed for calculation.
        The actual cost/revenue/profit calculations happen inside OptimizationMetrics.
        
        Returns:
            OptimizationMetrics containing raw parameters for calculation
            
        Raises:
            ValueError: If growth_days or field is None (invalid candidate)
        """
        if self.growth_days is None or self.field is None:
            raise ValueError("Cannot get metrics without growth_days and field")
        
        # Calculate area_used from field area if crop is provided
        area_used = None
        revenue_per_area = None
        max_revenue = None
        
        if self.crop is not None:
            # Use full field area for single-crop period optimization
            area_used = self.field.area
            revenue_per_area = self.crop.revenue_per_area
            max_revenue = self.crop.max_revenue
        
        return OptimizationMetrics(
            growth_days=self.growth_days,
            daily_fixed_cost=self.field.daily_fixed_cost,
            area_used=area_used,
            revenue_per_area=revenue_per_area,
            max_revenue=max_revenue,
            yield_factor=self.yield_factor,
        )
    
    @property
    def total_cost(self) -> Optional[float]:
        """Get total cost (convenience property for backward compatibility)."""
        if self.growth_days is None or self.field is None:
            return None
        return self.get_metrics().cost

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "start_date": self.start_date.isoformat(),
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "growth_days": self.growth_days,
            "total_cost": self.total_cost,
            "is_optimal": self.is_optimal,
            "yield_factor": self.yield_factor,
            "yield_loss_percentage": (1.0 - self.yield_factor) * 100.0,
        }
        
        # Add revenue and profit if available
        if self.growth_days is not None and self.field is not None:
            metrics = self.get_metrics()
            result["revenue"] = metrics.revenue
            result["profit"] = metrics.profit
        
        return result


@dataclass
class OptimalGrowthPeriodResponseDTO:
    """Response DTO containing optimal growth period calculation results."""

    crop_name: str
    variety: Optional[str]
    optimal_start_date: datetime
    completion_date: datetime
    growth_days: int
    total_cost: float
    revenue: Optional[float]
    profit: float
    daily_fixed_cost: float
    field: Field
    candidates: List[CandidateResultDTO]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "crop_name": self.crop_name,
            "variety": self.variety,
            "optimal_start_date": self.optimal_start_date.isoformat(),
            "completion_date": self.completion_date.isoformat(),
            "growth_days": self.growth_days,
            "total_cost": self.total_cost,
            "revenue": self.revenue,
            "profit": self.profit,
            "daily_fixed_cost": self.daily_fixed_cost,
            "field": {
                "field_id": self.field.field_id,
                "name": self.field.name,
                "area": self.field.area,
                "daily_fixed_cost": self.field.daily_fixed_cost,
                "location": self.field.location,
            },
            "candidates": [c.to_dict() for c in self.candidates],
        }

