"""Neighbor generator service for local search optimization."""

import random
from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.usecase.services.neighbor_operations import (
    NeighborOperation,
    FieldSwapOperation,
    FieldMoveOperation,
    FieldReplaceOperation,
    FieldRemoveOperation,
    CropInsertOperation,
    CropChangeOperation,
    PeriodReplaceOperation,
    QuantityAdjustOperation,
)


class NeighborGeneratorService:
    """Service to generate neighbor solutions for local search.
    
    This service orchestrates multiple neighbor operations and supports
    both exhaustive and sampled neighbor generation strategies.
    
    Design:
    - Strategy Pattern: Different operations implement NeighborOperation interface
    - Composition: Service composes multiple operations
    - Configuration: Behavior controlled by OptimizationConfig
    """
    
    def __init__(
        self,
        config: OptimizationConfig,
        operations: List[NeighborOperation] = None,
    ):
        """Initialize the neighbor generator service.
        
        Args:
            config: Optimization configuration
            operations: List of neighbor operations (if None, use default set)
        """
        self.config = config
        
        # Use provided operations or create default set
        if operations is None:
            self.operations = self._create_default_operations()
        else:
            self.operations = operations
    
    def _create_default_operations(self) -> List[NeighborOperation]:
        """Create the default set of neighbor operations."""
        return [
            FieldSwapOperation(),
            FieldMoveOperation(),
            FieldReplaceOperation(),
            FieldRemoveOperation(),
            CropInsertOperation(),
            CropChangeOperation(),
            PeriodReplaceOperation(),
            QuantityAdjustOperation(),
        ]
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        candidates: List[Any],
        fields: List[Field],
        crops: List[Crop],
    ) -> List[List[CropAllocation]]:
        """Generate neighbor solutions from current solution.
        
        Args:
            solution: Current allocation solution
            candidates: Allocation candidates
            fields: Available fields
            crops: Available crops
            
        Returns:
            List of neighbor solutions
        """
        # Prepare context for operations
        context = {
            "candidates": candidates,
            "fields": fields,
            "crops": crops,
            "config": self.config,
        }
        
        # Choose generation strategy
        if self.config.enable_neighbor_sampling:
            return self._generate_with_sampling(solution, context)
        else:
            return self._generate_all(solution, context)
    
    def _generate_all(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate all neighbors from all operations.
        
        Args:
            solution: Current solution
            context: Context information
            
        Returns:
            All generated neighbors
        """
        all_neighbors = []
        
        for operation in self.operations:
            neighbors = operation.generate_neighbors(solution, context)
            all_neighbors.extend(neighbors)
        
        return all_neighbors
    
    def _generate_with_sampling(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors with weighted sampling (Phase 1 optimization).
        
        Strategy:
        1. Generate neighbors from each operation
        2. Sample from each operation proportionally to weight
        3. Limit total neighbors to max_neighbors_per_iteration
        
        Args:
            solution: Current solution
            context: Context information
            
        Returns:
            Sampled neighbors
        """
        all_neighbors = []
        max_neighbors = self.config.max_neighbors_per_iteration
        
        # Calculate total weight
        operation_weights = self.config.operation_weights
        total_weight = sum(
            operation_weights.get(op.operation_name, op.default_weight)
            for op in self.operations
        )
        
        # Generate and sample from each operation
        for operation in self.operations:
            weight = operation_weights.get(operation.operation_name, operation.default_weight)
            target_size = int(max_neighbors * (weight / total_weight))
            
            if target_size == 0:
                continue
            
            # Generate neighbors from this operation
            op_neighbors = operation.generate_neighbors(solution, context)
            
            # Sample if too many
            if len(op_neighbors) > target_size:
                sampled = random.sample(op_neighbors, target_size)
            else:
                sampled = op_neighbors
            
            all_neighbors.extend(sampled)
        
        # Final sampling if still over limit
        if len(all_neighbors) > max_neighbors:
            all_neighbors = random.sample(all_neighbors, max_neighbors)
        
        return all_neighbors

