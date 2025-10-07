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
- candidates: List of all candidate evaluation results
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class CandidateResultDTO:
    """Evaluation result for a single candidate start date."""

    start_date: datetime
    completion_date: Optional[datetime]  # None if 100% not achieved
    growth_days: Optional[int]
    total_cost: Optional[float]  # None if calculation not possible
    is_optimal: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "start_date": self.start_date.isoformat(),
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "growth_days": self.growth_days,
            "total_cost": self.total_cost,
            "is_optimal": self.is_optimal,
        }


@dataclass
class OptimalGrowthPeriodResponseDTO:
    """Response DTO containing optimal growth period calculation results."""

    crop_name: str
    variety: Optional[str]
    optimal_start_date: datetime
    completion_date: datetime
    growth_days: int
    total_cost: float
    daily_fixed_cost: float
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
            "daily_fixed_cost": self.daily_fixed_cost,
            "candidates": [c.to_dict() for c in self.candidates],
        }

