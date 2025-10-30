"""Allocation result file gateway implementation.

Gateway implementation for loading allocation results from JSON files.
"""

import json
from typing import Optional
from datetime import datetime

from agrr_core.usecase.gateways.allocation_result_gateway import AllocationResultGateway
from agrr_core.entity.entities.multi_field_optimization_result_entity import (
    MultiFieldOptimizationResult,
)
from agrr_core.entity.entities.field_schedule_entity import FieldSchedule
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.adapter.interfaces.io.file_service_interface import FileServiceInterface

class AllocationResultFileGateway(AllocationResultGateway):
    """File-based gateway for allocation result operations."""
    
    def __init__(
        self,
        file_repository: FileServiceInterface,
        file_path: str = "",
    ):
        """Initialize with file repository and file path.
        
        Args:
            file_repository: File service for file I/O operations
            file_path: Path to the optimization result JSON file
        """
        self.file_repository = file_repository
        self.file_path = file_path
    
    def get_by_id(self, optimization_id: str) -> Optional[MultiFieldOptimizationResult]:
        """Get optimization result by ID.
        
        Note: This implementation loads from file and checks ID.
        For database-backed gateway, this would query by ID directly.
        
        Args:
            optimization_id: Unique identifier of the optimization result
            
        Returns:
            Optimization result entity if found and ID matches, None otherwise
        """
        result = self.get()
        if result and result.optimization_id == optimization_id:
            return result
        return None
    
    def get(self) -> Optional[MultiFieldOptimizationResult]:
        """Get optimization result from configured source (file in this implementation).
        
        Returns:
            Optimization result entity if file exists and is valid, None otherwise
        """
        if not self.file_path:
            return None
        
        try:
            # Read JSON file
            content = self.file_repository.read(self.file_path)
            data = json.loads(content)
            
            # Parse JSON to entity
            # Expected structure: {"optimization_result": {...}}
            if "optimization_result" not in data:
                raise ValueError("Missing 'optimization_result' field in JSON")
            
            result_data = data["optimization_result"]
            
            # Parse field schedules
            field_schedules = []
            for schedule_data in result_data.get("field_schedules", []):
                # Parse field - handle both nested and flat formats
                if "field" in schedule_data:
                    # Nested format: {"field": {"field_id": ...}}
                    field_dict = schedule_data["field"]
                    field = Field(
                        field_id=field_dict["field_id"],
                        name=field_dict["name"],
                        area=float(field_dict["area"]),
                        daily_fixed_cost=float(field_dict["daily_fixed_cost"]),
                        location=field_dict.get("location"),
                        fallow_period_days=field_dict.get("fallow_period_days", 28),
                    )
                else:
                    # Flat format: {"field_id": ..., "field_name": ...}
                    # Need to load field info from fields file or use defaults
                    field = Field(
                        field_id=schedule_data["field_id"],
                        name=schedule_data.get("field_name", schedule_data["field_id"]),
                        area=1000.0,  # Default, will be overridden if fields file is provided
                        daily_fixed_cost=5000.0,  # Default
                        fallow_period_days=28,  # Default
                    )
                
                # Parse allocations
                allocations = []
                for alloc_data in schedule_data.get("allocations", []):
                    # Parse crop - handle both nested and flat formats
                    if "crop" in alloc_data:
                        # Nested format: {"crop": {"crop_id": ...}}
                        crop_dict = alloc_data["crop"]
                        crop = Crop(
                            crop_id=crop_dict["crop_id"],
                            name=crop_dict["name"],
                            area_per_unit=float(crop_dict["area_per_unit"]),
                            variety=crop_dict.get("variety", ""),
                            revenue_per_area=float(crop_dict.get("revenue_per_area", 0.0)),
                            max_revenue=float(crop_dict.get("max_revenue", 0.0)),
                            groups=crop_dict.get("groups", []),
                        )
                    else:
                        # Flat format: {"crop_id": ..., "crop_name": ...}
                        crop = Crop(
                            crop_id=alloc_data["crop_id"],
                            name=alloc_data.get("crop_name", alloc_data["crop_id"]),
                            area_per_unit=0.5,  # Default
                            variety=alloc_data.get("variety", ""),
                            revenue_per_area=1000.0,  # Default
                            max_revenue=100000.0,  # Default
                            groups=[],  # Default
                        )
                    
                    # Parse dates
                    start_date = datetime.fromisoformat(alloc_data["start_date"].replace("Z", "+00:00"))
                    completion_date = datetime.fromisoformat(
                        alloc_data["completion_date"].replace("Z", "+00:00")
                    )
                    
                    allocation = CropAllocation(
                        allocation_id=alloc_data["allocation_id"],
                        field=field,
                        crop=crop,
                        area_used=float(alloc_data["area_used"]),
                        start_date=start_date,
                        completion_date=completion_date,
                        growth_days=int(alloc_data["growth_days"]),
                        accumulated_gdd=float(alloc_data.get("accumulated_gdd", 0.0)),
                        total_cost=float(alloc_data["total_cost"]),
                        expected_revenue=float(alloc_data.get("expected_revenue", 0.0)),
                        profit=float(alloc_data.get("profit", 0.0)),
                    )
                    allocations.append(allocation)
                
                # Create field schedule
                schedule = FieldSchedule(
                    field=field,
                    allocations=allocations,
                    total_area_used=float(schedule_data.get("total_area_used", sum(a.area_used for a in allocations))),
                    total_cost=float(schedule_data["total_cost"]),
                    total_revenue=float(schedule_data["total_revenue"]),
                    total_profit=float(schedule_data["total_profit"]),
                    utilization_rate=float(schedule_data["utilization_rate"]),
                )
                field_schedules.append(schedule)
            
            # Parse crop areas
            crop_areas = {
                crop_id: float(area)
                for crop_id, area in result_data.get("crop_areas", {}).items()
            }
            
            # Create optimization result entity
            result = MultiFieldOptimizationResult(
                optimization_id=result_data["optimization_id"],
                field_schedules=field_schedules,
                total_cost=float(result_data["total_cost"]),
                total_revenue=float(result_data["total_revenue"]),
                total_profit=float(result_data["total_profit"]),
                crop_areas=crop_areas,
                optimization_time=float(result_data.get("optimization_time", 0.0)),
                algorithm_used=result_data.get("algorithm_used", "unknown"),
                is_optimal=result_data.get("is_optimal", False),
            )
            
            return result
            
        except FileNotFoundError:
            return None
        except Exception as e:
            # Handle FileError and other exceptions
            if "FILE_ERROR" in str(e) or "No such file" in str(e):
                return None
            if isinstance(e, (json.JSONDecodeError, KeyError, ValueError)):
                raise ValueError(f"Invalid optimization result file format: {e}")
            # Re-raise unknown exceptions
            raise

