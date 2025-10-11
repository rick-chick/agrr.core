"""Multi-field crop allocation request DTO.

Request DTO for optimizing crop allocation across multiple fields.

Fields:
- field_ids: List of field IDs to consider for allocation
- crop_requirements: List of crop requirements (crop_id, variety, targets)
- planning_period_start: Start date of planning period
- planning_period_end: End date of planning period
- weather_data_file: Path to weather data file
- optimization_objective: Optimization objective ("maximize_profit" or "minimize_cost")
- max_computation_time: Maximum computation time in seconds (None for no limit)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class CropRequirementSpec:
    """Specification for a single crop's requirements."""
    
    crop_id: str
    variety: Optional[str] = None
    min_quantity: Optional[float] = None
    target_quantity: Optional[float] = None
    max_quantity: Optional[float] = None
    crop_requirement_file: Optional[str] = None  # Path to pre-generated requirement file


@dataclass
class MultiFieldCropAllocationRequestDTO:
    """Request DTO for multi-field, multi-crop allocation optimization."""

    field_ids: List[str]
    crop_requirements: List[CropRequirementSpec]
    planning_period_start: datetime
    planning_period_end: datetime
    weather_data_file: str
    optimization_objective: str = "maximize_profit"  # or "minimize_cost"
    max_computation_time: Optional[float] = None  # seconds

    def __post_init__(self):
        """Validate request parameters."""
        if not self.field_ids:
            raise ValueError("field_ids must not be empty")
        
        if not self.crop_requirements:
            raise ValueError("crop_requirements must not be empty")
        
        if self.planning_period_start >= self.planning_period_end:
            raise ValueError(
                f"planning_period_start ({self.planning_period_start}) must be before "
                f"planning_period_end ({self.planning_period_end})"
            )
        
        if self.optimization_objective not in ["maximize_profit", "minimize_cost"]:
            raise ValueError(
                f"optimization_objective must be 'maximize_profit' or 'minimize_cost', "
                f"got '{self.optimization_objective}'"
            )
        
        if self.max_computation_time is not None and self.max_computation_time <= 0:
            raise ValueError(
                f"max_computation_time must be positive, got {self.max_computation_time}"
            )
        
        # Validate crop requirements
        for crop_req in self.crop_requirements:
            if crop_req.min_quantity is not None and crop_req.min_quantity < 0:
                raise ValueError(f"min_quantity must be non-negative for {crop_req.crop_id}")
            
            if crop_req.target_quantity is not None and crop_req.target_quantity < 0:
                raise ValueError(f"target_quantity must be non-negative for {crop_req.crop_id}")
            
            if crop_req.max_quantity is not None and crop_req.max_quantity < 0:
                raise ValueError(f"max_quantity must be non-negative for {crop_req.crop_id}")
            
            # Validate quantity ordering
            if (crop_req.min_quantity is not None and 
                crop_req.target_quantity is not None and 
                crop_req.min_quantity > crop_req.target_quantity):
                raise ValueError(
                    f"min_quantity ({crop_req.min_quantity}) must be <= "
                    f"target_quantity ({crop_req.target_quantity}) for {crop_req.crop_id}"
                )
            
            if (crop_req.target_quantity is not None and 
                crop_req.max_quantity is not None and 
                crop_req.target_quantity > crop_req.max_quantity):
                raise ValueError(
                    f"target_quantity ({crop_req.target_quantity}) must be <= "
                    f"max_quantity ({crop_req.max_quantity}) for {crop_req.crop_id}"
                )

