"""Multi-field crop allocation response DTO.

Response DTO containing the optimization result.

Fields:
- optimization_result: The complete optimization result entity
- summary: Human-readable summary statistics
"""

from dataclasses import dataclass
from typing import Dict, Any

from agrr_core.entity.entities.multi_field_optimization_result_entity import MultiFieldOptimizationResult

@dataclass
class MultiFieldCropAllocationResponseDTO:
    """Response DTO for multi-field, multi-crop allocation optimization."""

    optimization_result: MultiFieldOptimizationResult

    @property
    def summary(self) -> Dict[str, Any]:
        """Get human-readable summary of optimization result."""
        result = self.optimization_result
        
        return {
            "optimization_id": result.optimization_id,
            "algorithm_used": result.algorithm_used,
            "is_optimal": result.is_optimal,
            "computation_time_seconds": result.optimization_time,
            "total_fields": result.total_fields,
            "total_allocations": result.total_allocations,
            "total_cost": result.total_cost,
            "total_revenue": result.total_revenue,
            "total_profit": result.total_profit,
            "profit_rate_percent": result.profit_rate * 100,
            "average_field_utilization_percent": result.average_field_utilization,
            "crop_diversity": result.crop_diversity,
            "crop_areas": result.crop_areas,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = self.optimization_result
        
        return {
            "optimization_result": {
                "optimization_id": result.optimization_id,
                "algorithm_used": result.algorithm_used,
                "is_optimal": result.is_optimal,
                "optimization_time": result.optimization_time,
                "total_cost": result.total_cost,
                "total_revenue": result.total_revenue,
                "total_profit": result.total_profit,
                "crop_areas": result.crop_areas,
                "field_schedules": [
                    {
                        "field_id": schedule.field.field_id,
                        "field_name": schedule.field.name,
                        "total_area_used": schedule.total_area_used,
                        "total_cost": schedule.total_cost,
                        "total_revenue": schedule.total_revenue,
                        "total_profit": schedule.total_profit,
                        "utilization_rate": schedule.utilization_rate,
                        "allocation_count": schedule.allocation_count,
                        "allocations": [
                            {
                                "allocation_id": alloc.allocation_id,
                                "crop_id": alloc.crop.crop_id,
                                "crop_name": alloc.crop.name,
                                "variety": alloc.crop.variety,
                                "area_used": alloc.area_used,
                                "start_date": alloc.start_date.isoformat(),
                                "completion_date": alloc.completion_date.isoformat(),
                                "growth_days": alloc.growth_days,
                                "accumulated_gdd": alloc.accumulated_gdd,
                                "total_cost": alloc.total_cost,
                                "expected_revenue": alloc.expected_revenue,
                                "profit": alloc.profit,
                            }
                            for alloc in schedule.allocations
                        ],
                    }
                    for schedule in result.field_schedules
                ],
            },
            "summary": self.summary,
        }

