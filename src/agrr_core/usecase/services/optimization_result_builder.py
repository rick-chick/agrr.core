"""Service for building optimization results.

This service constructs the final optimization result from allocations,
calculating all necessary metrics and creating the appropriate entity structures.
"""

import uuid
from typing import List, Dict, Any

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_schedule_entity import FieldSchedule
from agrr_core.entity.entities.multi_field_optimization_result_entity import (
    MultiFieldOptimizationResult,
)


class OptimizationResultBuilder:
    """Build optimization results from allocations.
    
    Responsibilities:
    - Group allocations by field
    - Calculate field-level metrics (cost, revenue, profit, utilization)
    - Calculate global metrics
    - Build FieldSchedule entities
    - Build MultiFieldOptimizationResult entity
    
    Design Pattern:
    - Builder Pattern: Step-by-step result construction
    - Aggregation: Collect and aggregate metrics
    """
    
    def build(
        self,
        allocations: List[CropAllocation],
        fields: List[Field],
        computation_time: float,
        algorithm_used: str,
    ) -> MultiFieldOptimizationResult:
        """Build complete optimization result from allocations.
        
        Args:
            allocations: Final allocation solution
            fields: All fields used in optimization
            computation_time: Time spent on optimization (seconds)
            algorithm_used: Name of algorithm used (e.g., "Greedy + Local Search")
            
        Returns:
            Complete MultiFieldOptimizationResult entity
            
        Example:
            >>> builder = OptimizationResultBuilder()
            >>> result = builder.build(allocations, fields, 5.2, "Greedy")
            >>> result.total_profit
            1500000.0
        """
        # Group allocations by field
        field_allocations = self._group_by_field(allocations, fields)
        
        # Build field schedules and aggregate metrics
        field_schedules = []
        global_metrics = {
            'total_cost': 0.0,
            'total_revenue': 0.0,
            'total_profit': 0.0,
            'crop_areas': {},
        }
        
        for field in fields:
            field_allocs = field_allocations[field.field_id]
            
            # Calculate field-level metrics
            field_metrics = self._calculate_field_metrics(field, field_allocs)
            
            # Create field schedule entity
            field_schedule = FieldSchedule(
                field=field,
                allocations=field_allocs,
                total_area_used=field_metrics['area_used'],
                total_cost=field_metrics['cost'],
                total_revenue=field_metrics['revenue'],
                total_profit=field_metrics['profit'],
                utilization_rate=field_metrics['utilization'],
            )
            field_schedules.append(field_schedule)
            
            # Aggregate to global metrics
            self._aggregate_metrics(global_metrics, field_allocs, field_metrics)
        
        # Build final result entity
        return MultiFieldOptimizationResult(
            optimization_id=str(uuid.uuid4()),
            field_schedules=field_schedules,
            total_cost=global_metrics['total_cost'],
            total_revenue=global_metrics['total_revenue'],
            total_profit=global_metrics['total_profit'],
            crop_areas=global_metrics['crop_areas'],
            optimization_time=computation_time,
            algorithm_used=algorithm_used,
            is_optimal=False,  # Heuristic algorithms don't guarantee optimality
        )
    
    def _group_by_field(
        self,
        allocations: List[CropAllocation],
        fields: List[Field],
    ) -> Dict[str, List[CropAllocation]]:
        """Group allocations by field ID.
        
        Args:
            allocations: All allocations
            fields: All fields
            
        Returns:
            Dictionary mapping field_id to list of allocations
        """
        # Initialize with empty lists for all fields
        field_allocations: Dict[str, List[CropAllocation]] = {
            f.field_id: [] for f in fields
        }
        
        # Group allocations
        for alloc in allocations:
            field_allocations[alloc.field.field_id].append(alloc)
        
        return field_allocations
    
    def _calculate_field_metrics(
        self,
        field: Field,
        allocations: List[CropAllocation],
    ) -> Dict[str, float]:
        """Calculate metrics for a single field.
        
        Metrics:
        - cost: Total cost of all allocations
        - revenue: Total revenue of all allocations
        - profit: Total profit of all allocations
        - area_used: Total area used by allocations
        - utilization: Percentage of field area used
        
        Args:
            field: Field entity
            allocations: Allocations in this field
            
        Returns:
            Dictionary with calculated metrics
        """
        cost = sum(a.total_cost for a in allocations)
        revenue = sum(
            a.expected_revenue for a in allocations 
            if a.expected_revenue is not None
        )
        profit = sum(
            a.profit for a in allocations 
            if a.profit is not None
        )
        area_used = sum(a.area_used for a in allocations)
        utilization = (area_used / field.area * 100) if field.area > 0 else 0.0
        
        return {
            'cost': cost,
            'revenue': revenue,
            'profit': profit,
            'area_used': area_used,
            'utilization': utilization,
        }
    
    def _aggregate_metrics(
        self,
        global_metrics: Dict[str, Any],
        allocations: List[CropAllocation],
        field_metrics: Dict[str, float],
    ) -> None:
        """Aggregate field metrics to global metrics.
        
        This method modifies global_metrics in-place.
        
        Args:
            global_metrics: Global metrics dictionary (modified in-place)
            allocations: Allocations from a field
            field_metrics: Calculated field metrics
        """
        # Aggregate financial metrics
        global_metrics['total_cost'] += field_metrics['cost']
        global_metrics['total_revenue'] += field_metrics['revenue']
        global_metrics['total_profit'] += field_metrics['profit']
        
        # Aggregate crop quantities
        for alloc in allocations:
            crop_id = alloc.crop.crop_id
            if crop_id not in global_metrics['crop_areas']:
                global_metrics['crop_areas'][crop_id] = 0.0
            global_metrics['crop_areas'][crop_id] += alloc.area_used

