"""Multi-field crop allocation interactor using greedy or DP algorithm with local search.

This interactor implements two allocation strategies:
1. Greedy + Local Search (Hill Climbing) - fast heuristic approach
2. DP (per-field) + Local Search - optimal per-field solution with global adjustment

Greedy Algorithm:
1. Generate candidates: For each field × crop × start date, generate allocation candidates
2. Greedy allocation: Select allocations in profit-rate descending order
3. Local search: Improve solution using Swap, Shift, and Replace operations
4. Return optimized solution

DP Algorithm:
1. Generate candidates: For each field × crop × start date, generate allocation candidates
2. Per-field DP: Solve weighted interval scheduling for each field independently
3. Revenue recalculation: Recalculate revenue with market demand budget tracking
4. Local search: Improve solution using Swap, Shift, and Replace operations
5. Return optimized solution

Time Complexity: 
- Greedy: O(n log n + k·n²) where n is number of candidates, k is LS iterations
- DP: O(n log n + m·n² + k·n²) where m is number of fields, k is LS iterations

Expected Quality: 
- Greedy: 85-95% of optimal solution
- DP: 95-100% per-field optimal (global optimality depends on market demand limits)

Optimizations (Phase 1-3):
- Phase 1: Configuration, neighbor sampling, candidate filtering
- Phase 2: Parallel candidate generation, incremental feasibility
- Phase 3: Adaptive early stopping
"""

import time
import uuid

import dataclasses
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_schedule_entity import FieldSchedule
from agrr_core.entity.entities.multi_field_optimization_result_entity import MultiFieldOptimizationResult
from agrr_core.usecase.dto.multi_field_crop_allocation_request_dto import (
    MultiFieldCropAllocationRequestDTO,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_response_dto import (
    MultiFieldCropAllocationResponseDTO,
)
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.interactors.growth_period_optimize_interactor import GrowthPeriodOptimizeInteractor
from agrr_core.usecase.dto.growth_period_optimize_request_dto import OptimalGrowthPeriodRequestDTO
from agrr_core.usecase.services.neighbor_generator_service import NeighborGeneratorService
from agrr_core.usecase.interactors.base_optimizer import BaseOptimizer
from agrr_core.entity.value_objects.optimization_objective import OptimizationMetrics
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.usecase.services.interaction_rule_service import InteractionRuleService
from agrr_core.usecase.services.alns_optimizer_service import ALNSOptimizer
from agrr_core.usecase.services.violation_checker_service import ViolationCheckerService

@dataclass
class AllocationCandidate:
    """Candidate for crop allocation (internal use).
    
    Implements Optimizable protocol for unified optimization.
    This class holds entities and raw parameters for metric calculation.
    """
    
    field: Field
    crop: Crop
    start_date: datetime
    completion_date: datetime
    growth_days: int
    accumulated_gdd: float
    area_used: float  # Allocated area (m²)
    
    def get_metrics(
        self, 
        current_allocations: Optional[List[CropAllocation]] = None,
        field_schedules: Optional[Dict[str, List[CropAllocation]]] = None,
        interaction_rules: Optional[List] = None
    ) -> OptimizationMetrics:
        """Get optimization metrics with raw calculation parameters (implements Optimizable protocol).
        
        Returns OptimizationMetrics with all raw data needed for calculation.
        The actual cost/revenue/profit calculations happen inside OptimizationMetrics.
        
        Uses OptimizationMetrics.create_for_allocation() which automatically calculates:
        - crop_cumulative_revenue from current_allocations
        - interaction_impact from field_schedules and interaction_rules
        
        This is the SINGLE SOURCE OF TRUTH for all profit-related calculations.
        
        Args:
            current_allocations: List of currently selected allocations (for market demand tracking)
            field_schedules: Dict mapping field_id to allocations (for interaction rules)
            interaction_rules: List of interaction rules (for continuous cultivation, etc.)
            
        Returns:
            OptimizationMetrics containing raw parameters for calculation
        """
        # Use factory method - all calculations are performed internally
        return OptimizationMetrics.create_for_allocation(
            area_used=self.area_used,
            revenue_per_area=self.crop.revenue_per_area,
            max_revenue=self.crop.max_revenue,
            growth_days=self.growth_days,
            daily_fixed_cost=self.field.daily_fixed_cost,
            crop_id=self.crop.crop_id,
            crop=self.crop,
            field=self.field,
            start_date=self.start_date,
            current_allocations=current_allocations,
            field_schedules=field_schedules,
            interaction_rules=interaction_rules,
        )
    
    # ===== Baseline Properties (NO CONTEXT - for filtering only) =====
    # These should NOT be used for final calculations
    # Use OptimizationMetrics.create_for_allocation() with context instead
    
    @property
    def cost(self) -> float:
        """Get baseline cost (NO CONTEXT - for pre-allocation filtering only)."""
        return self.get_metrics().cost
    
    @property
    def revenue(self) -> Optional[float]:
        """Get baseline revenue (NO CONTEXT - for pre-allocation filtering only)."""
        return self.get_metrics().revenue
    
    @property
    def profit(self) -> float:
        """Get baseline profit (NO CONTEXT - for pre-allocation filtering only)."""
        return self.get_metrics().profit
    
    @property
    def profit_rate(self) -> float:
        """Get baseline profit rate (NO CONTEXT - for pre-allocation filtering only)."""
        metrics = self.get_metrics()
        return (metrics.profit / metrics.cost) if metrics.cost > 0 else 0.0
    
    def overlaps_with_fallow(self, other) -> bool:
        """Check if this candidate overlaps with another including fallow period.
        
        This method checks if two candidates/allocations violate the fallow period constraint.
        The fallow period is the required rest period for the soil after crop harvest.
        
        Args:
            other: Another candidate or allocation to check overlap with
                   (AllocationCandidate or CropAllocation)
            
        Returns:
            True if candidates overlap considering fallow period, False otherwise
            
        Example:
            If candidate1 completes on June 30 and field has 28-day fallow period,
            candidate2 must start on or after July 28.
        """
        from datetime import timedelta
        
        # Only check overlap if both candidates are in the same field
        if self.field.field_id != other.field.field_id:
            return False
        
        # Calculate end dates including fallow period
        self_end_with_fallow = self.completion_date + timedelta(
            days=self.field.fallow_period_days
        )
        other_end_with_fallow = other.completion_date + timedelta(
            days=other.field.fallow_period_days
        )
        
        # Check overlap with fallow periods included
        return not (self_end_with_fallow <= other.start_date or 
                    other_end_with_fallow <= self.start_date)

class MultiFieldCropAllocationGreedyInteractor(BaseOptimizer[AllocationCandidate]):
    """Interactor for multi-field crop allocation using greedy + local search.
    
    Optimizations:
    - Phase 1: Configurable parameters, neighbor sampling, candidate filtering
    - Phase 2: Parallel candidate generation, incremental feasibility
    - Phase 3: Adaptive early stopping
    
    Uses unified optimization objective via BaseOptimizer.
    """

    def __init__(
        self,
        field_gateway: FieldGateway,
        crop_gateway: CropProfileGateway,
        weather_gateway: WeatherGateway,
        crop_profile_gateway_internal: CropProfileGateway,
        config: Optional[OptimizationConfig] = None,
        interaction_rules: Optional[List[InteractionRule]] = None,
    ):
        super().__init__()  # Initialize BaseOptimizer
        self.field_gateway = field_gateway
        self.crop_gateway = crop_gateway
        self.weather_gateway = weather_gateway
        self.config = config or OptimizationConfig()
        
        # Inject crop_profile_gateway for growth period optimizer
        # (This should be an in-memory gateway instance created by Adapter/Controller layer)
        self.crop_profile_gateway_internal = crop_profile_gateway_internal
        
        # Create growth period optimizer for candidate generation
        self.growth_period_optimizer = GrowthPeriodOptimizeInteractor(
            crop_profile_gateway=self.crop_profile_gateway_internal,
            weather_gateway=weather_gateway,
        )
        
        # Create neighbor generator service (Phase 1 refactoring)
        self.neighbor_generator = NeighborGeneratorService(self.config)
        
        # Create interaction rule service (for continuous cultivation impact)
        self.interaction_rule_service = InteractionRuleService(
            rules=interaction_rules or []
        )
        
        # Create violation checker service
        self.violation_checker = ViolationCheckerService(
            interaction_rule_service=self.interaction_rule_service
        )
        
        # Create ALNS optimizer if enabled
        self.alns_optimizer = ALNSOptimizer(self.config) if self.config.enable_alns else None

    def execute(
        self,
        request: MultiFieldCropAllocationRequestDTO,
        enable_local_search: bool = True,
        max_local_search_iterations: Optional[int] = None,
        config: Optional[OptimizationConfig] = None,
        algorithm: str = "dp",
    ) -> MultiFieldCropAllocationResponseDTO:
        """Execute multi-field crop allocation optimization.
        
        Args:
            request: Allocation request
            enable_local_search: If True, apply local search after initial allocation
            max_local_search_iterations: Maximum iterations for local search (overrides config)
            config: Optimization configuration (overrides instance config)
            algorithm: Algorithm to use for initial allocation ("dp" or "greedy"). Default: "dp"
            
        Returns:
            Optimization response with allocation solution
        """
        start_time = time.time()
        
        # Validate algorithm parameter
        if algorithm not in ["greedy", "dp"]:
            raise ValueError(f"Invalid algorithm: {algorithm}. Must be 'greedy' or 'dp'")
        
        # Use provided config or instance config
        optimization_config = config or self.config
        
        # Override max_iterations if explicitly provided
        if max_local_search_iterations is not None:
            optimization_config.max_local_search_iterations = max_local_search_iterations
        
        # Phase 1: Load crops and fields
        fields = self._load_fields(request.field_ids)
        crops = self.crop_gateway.get_all()
        
        # Phase 1: Generate candidates based on strategy
        if optimization_config.candidate_generation_strategy == "period_template":
            # Use Period Template strategy
            candidates = self._generate_candidates_with_period_template(
                fields, crops, request, optimization_config, algorithm
            )
        else:
            # Use legacy candidate pool strategy
            if optimization_config.enable_parallel_candidate_generation:
                candidates = self._generate_candidates_parallel(fields, crops, request, optimization_config)
            else:
                candidates = self._generate_candidates(fields, crops, request, optimization_config)
        
        # Check if any candidates were generated
        if not candidates:
            # All crops failed to generate candidates
            # This means no crop can complete growth in the planning period
            raise ValueError(
                "No valid allocation candidates could be generated.\n"
                "\n"
                "Possible causes:\n"
                "1. Planning period is too short for any crop to complete growth\n"
                "2. Weather data is insufficient (extends beyond available data)\n"
                "3. All crops require temperature conditions not met in the planning period\n"
                "   (e.g., summer crops cannot grow in winter starting period)\n"
                "\n"
                "Recommendations:\n"
                "- Extend planning period end date\n"
                "- Choose crops suitable for the season\n"
                "- Provide more weather data (historical or predicted)\n"
                "- Adjust planning start date to a suitable season for your crops"
            )
        
        # Store planning start date for soil recovery calculation
        planning_start_date = request.planning_period_start
        
        # Phase 2: Initial allocation (Greedy or DP)
        if algorithm == "dp":
            allocations = self._dp_allocation(candidates, crops, fields, planning_start_date)
            algorithm_name = "DP"
        else:  # greedy
            allocations = self._greedy_allocation(
                candidates, 
                crops,
                request.optimization_objective,
                planning_start_date
            )
            algorithm_name = "Greedy"
        
        # Phase 3: Local search (optional)
        if enable_local_search:
            allocations = self._local_search(
                allocations,
                candidates,
                fields=fields,
                config=optimization_config,
                time_limit=request.max_computation_time,
                planning_start_date=planning_start_date
            )
            # Update algorithm name based on which search was used
            if optimization_config.enable_alns:
                algorithm_name += " + ALNS"
            else:
                algorithm_name += " + Local Search"
        
        # Phase 4: Build result
        computation_time = time.time() - start_time
        result = self._build_result(
            allocations=allocations,
            fields=fields,
            computation_time=computation_time,
            algorithm_used=algorithm_name,
        )
        
        return MultiFieldCropAllocationResponseDTO(optimization_result=result)

    def _load_fields(self, field_ids: List[str]) -> List[Field]:
        """Load field entities from gateway."""
        fields = []
        for field_id in field_ids:
            field = self.field_gateway.get(field_id)
            if field is None:
                raise ValueError(f"Field not found: {field_id}")
            fields.append(field)
        return fields

    def _generate_candidates(
        self,
        fields: List[Field],
        crops: List,
        request: MultiFieldCropAllocationRequestDTO,
        config: Optional[OptimizationConfig] = None,
    ) -> List[AllocationCandidate]:
        """Generate allocation candidates for all field × crop × area combinations.
        
        For each field and crop, use the existing GrowthPeriodOptimizeInteractor
        to find all viable cultivation periods (DP-optimized).
        
        With filtering (Phase 1): Remove low-quality candidates early.
        """
        cfg = config or self.config
        candidates = []
        
        for field in fields:
            for crop_aggregate in crops:
                crop = crop_aggregate.crop
                
                # Use GrowthPeriodOptimizeInteractor to find all viable periods (DP)
                optimization_request = OptimalGrowthPeriodRequestDTO(
                    crop_id=crop.crop_id,
                    variety=crop.variety,
                    evaluation_period_start=request.planning_period_start,
                    evaluation_period_end=request.planning_period_end,
                    field=field,
                    filter_redundant_candidates=request.filter_redundant_candidates,  # Pass flag from parent request
                )
                
                # Set crop requirement in growth period optimizer gateway
                self.crop_profile_gateway_internal.save(crop_aggregate)
                
                optimization_result = self.growth_period_optimizer.execute(optimization_request)
                
                # Clean up
                self.crop_profile_gateway_internal.delete()
                
                # Calculate maximum area that can fit in the field
                field_max_area = field.area
                
                # Generate candidates for each area level
                for area_level in cfg.area_levels:
                    area_used = field_max_area * area_level
                    
                    # Use top N period candidates from DP results
                    for candidate_period in optimization_result.candidates[:cfg.top_period_candidates]:
                        if candidate_period.completion_date is None or candidate_period.total_cost is None:
                            continue  # Skip incomplete candidates
                        
                        # Create candidate with entities (no calculation - just pass data)
                        candidate = AllocationCandidate(
                            field=field,
                            crop=crop,
                            start_date=candidate_period.start_date,
                            completion_date=candidate_period.completion_date,
                            growth_days=candidate_period.growth_days,
                            accumulated_gdd=0.0,  # Will be filled if needed
                            area_used=area_used,
                        )
                        
                        # ===== ⚠️ LEGACY FILTERING CODE - DO NOT REPLICATE =====
                        # This filtering logic is DISABLED by default (enable_candidate_filtering=False)
                        # because economic filtering often excludes ALL viable candidates in real-world scenarios.
                        # 
                        # IMPORTANT: New implementations should NOT copy this pattern.
                        # This code is kept only for backward compatibility with legacy behavior.
                        # 
                        # See OptimizationConfig.enable_candidate_filtering documentation for rationale.
                        # See Period Template implementation (_generate_candidates_with_period_template)
                        # for the correct approach (no filtering).
                        # ===== Phase 1: Quality Filtering (LEGACY - NOT RECOMMENDED) =====
                        if cfg.enable_candidate_filtering:
                            # Get baseline metrics (no context - this is pre-allocation filtering)
                            baseline_metrics = candidate.get_metrics()
                            
                            # Filter 1: Minimum profit rate
                            cost = baseline_metrics.cost
                            profit = baseline_metrics.profit
                            profit_rate = (profit / cost) if cost > 0 else 0.0
                            if profit_rate < cfg.min_profit_rate_threshold:
                                continue  # Skip clearly bad candidates
                            
                            # Filter 2: Minimum revenue/cost ratio
                            revenue = baseline_metrics.revenue
                            if revenue is not None and cost > 0:
                                revenue_cost_ratio = revenue / cost
                                if revenue_cost_ratio < cfg.min_revenue_cost_ratio:
                                    continue
                            
                            # Filter 3: Minimum absolute profit (for profit maximization)
                            if request.optimization_objective == "maximize_profit":
                                if profit < 0:
                                    continue  # Skip unprofitable candidates
                        
                        candidates.append(candidate)
        
        # ===== LEGACY POST-FILTERING - DO NOT REPLICATE =====
        # See warning above about legacy filtering code.
        if cfg.enable_candidate_filtering and cfg.max_candidates_per_field_crop > 0:
            candidates = self._post_filter_candidates(candidates, cfg)
        
        return candidates
    
    def _generate_candidates_parallel(
        self,
        fields: List[Field],
        crops: List,
        request: MultiFieldCropAllocationRequestDTO,
        config: OptimizationConfig,
    ) -> List[AllocationCandidate]:
        """Generate candidates in parallel for all field×crop combinations (Phase 2).
        
        This significantly speeds up candidate generation by parallelizing DP optimization.
        Expected speedup: 20-50x for typical problems.
        """
        
        # Create tasks for all field × crop combinations
        tasks = []
        for field in fields:
            for crop_aggregate in crops:
                task = self._generate_candidates_for_field_crop(
                    field, crop_aggregate, request, config
                )
                tasks.append(task)
        
        # Execute all tasks in parallel
        candidate_lists = asyncio.gather(*tasks)
        
        # Flatten results
        all_candidates = []
        for candidate_list in candidate_lists:
            all_candidates.extend(candidate_list)
        
        # ===== LEGACY POST-FILTERING - DO NOT REPLICATE =====
        # See _generate_candidates() for warning about legacy filtering code.
        if config.enable_candidate_filtering and config.max_candidates_per_field_crop > 0:
            all_candidates = self._post_filter_candidates(all_candidates, config)
        
        return all_candidates
    
    def _generate_candidates_with_period_template(
        self,
        fields: List[Field],
        crops: List,
        request: MultiFieldCropAllocationRequestDTO,
        config: OptimizationConfig,
        algorithm: str,
    ) -> List[AllocationCandidate]:
        """Generate candidates using Period Template strategy (recommended).
        
        Memory efficient: Generates Crop × Period templates using GrowthPeriodOptimizeInteractor,
        then applies them to fields dynamically.
        
        Args:
            fields: List of fields
            crops: List of crop aggregates
            request: Allocation request
            config: Optimization config
            algorithm: Algorithm name ("greedy" or "dp")
            
        Returns:
            List of AllocationCandidate
        """
        from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
            OptimalGrowthPeriodRequestDTO
        )
        from agrr_core.entity.entities.period_template_entity import PeriodTemplate
        
        # Generate period templates for each crop using GrowthPeriodOptimizeInteractor
        # Use a single "reference field" for template generation (templates are field-independent)
        reference_field = fields[0] if fields else Field(
            field_id="template_field",
            name="Template Reference Field",
            area=1000.0,
            daily_fixed_cost=0.0
        )
        
        templates_by_crop = {}
        
        for crop_aggregate in crops:
            crop = crop_aggregate.crop
            
            # Generate templates for this crop using GrowthPeriodOptimizeInteractor
            optimization_request = OptimalGrowthPeriodRequestDTO(
                crop_id=crop.crop_id,
                variety=crop.variety,
                evaluation_period_start=request.planning_period_start,
                evaluation_period_end=request.planning_period_end,
                field=reference_field,
                filter_redundant_candidates=False,  # We want all possible templates
            )
            
            # Set crop requirement in growth period optimizer gateway
            self.crop_profile_gateway_internal.save(crop_aggregate)
            
            try:
                optimization_result = self.growth_period_optimizer.execute(optimization_request)
                
                # Convert CandidateResultDTO to PeriodTemplate using factory method
                templates = []
                limit = min(len(optimization_result.candidates), config.max_templates_per_crop)
                
                for assessment in optimization_result.candidates[:limit]:
                    template = PeriodTemplate.from_candidate_result(
                        candidate=assessment,
                        crop=crop,
                        accumulated_gdd=0.0  # TODO: Add accumulated_gdd to CandidateResultDTO
                    )
                    if template is not None:
                        templates.append(template)
                
                templates_by_crop[crop.crop_id] = templates
                
            except ValueError as e:
                # Crop cannot complete growth in the planning period
                templates_by_crop[crop.crop_id] = []
        
        # Generate candidates by applying templates to fields
        candidates = []
        area_levels = config.area_levels or [1.0]
        
        # Determine template limit based on algorithm
        template_limits = {
            "greedy": 50,
            "dp": 200,
        }
        limit = template_limits.get(algorithm, 50)
        
        for crop_aggregate in crops:
            crop = crop_aggregate.crop
            templates = templates_by_crop.get(crop.crop_id, [])
            
            # Use top N templates
            for template in templates[:limit]:
                for field in fields:
                    for area_level in area_levels:
                        area = field.area * area_level
                        
                        # Dynamically apply template to field
                        candidate = template.apply_to_field(
                            field=field,
                            area_used=area
                        )
                        
                        # No filtering: Let optimizer handle all candidates
                        # Economic filtering often excludes all viable candidates in real-world scenarios
                        # (see OptimizationConfig.enable_candidate_filtering documentation)
                        candidates.append(candidate)
        
        return candidates
    
    def _generate_candidates_for_field_crop(
        self,
        field: Field,
        crop_aggregate,
        request: MultiFieldCropAllocationRequestDTO,
        config: OptimizationConfig,
    ) -> List[AllocationCandidate]:
        """Generate candidates for a single field×crop combination.
        
        This is used by parallel candidate generation.
        
        Returns:
            List of allocation candidates. Returns empty list if the crop
            cannot be grown in the given planning period (graceful degradation).
            
        Note:
            This method catches ValueError from GrowthPeriodOptimizeInteractor
            to allow partial allocation when some crops cannot complete growth.
            The final check in execute() ensures at least one crop succeeds.
        """
        crop = crop_aggregate.crop
        
        # DP optimization for this field×crop
        optimization_request = OptimalGrowthPeriodRequestDTO(
            crop_id=crop.crop_id,
            variety=crop.variety,
            evaluation_period_start=request.planning_period_start,
            evaluation_period_end=request.planning_period_end,
            field=field,
            filter_redundant_candidates=request.filter_redundant_candidates,  # Pass flag from parent request
        )
        
        # Set crop requirement in growth period optimizer gateway
        self.crop_profile_gateway_internal.save(crop_aggregate)
        
        try:
            optimization_result = self.growth_period_optimizer.execute(optimization_request)
            
        except ValueError as e:
            # Crop cannot complete growth in the planning period
            # This is expected behavior for some crop-season combinations
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Skipping crop '{crop.name} ({crop.variety})' in field '{field.name}': {str(e)}"
            )
            
            # Clean up before returning
            self.crop_profile_gateway_internal.delete()
            
            # Return empty list to skip this crop
            return []
            
        finally:
            # Ensure cleanup happens even if unexpected error occurs
            try:
                self.crop_profile_gateway_internal.delete()
            except Exception:
                pass  # Ignore cleanup errors
        
        # Generate area×period candidates
        candidates = []
        field_max_area = field.area
        
        for area_level in config.area_levels:
            area_used = field_max_area * area_level
            
            for candidate_period in optimization_result.candidates[:config.top_period_candidates]:
                if candidate_period.completion_date is None:
                    continue
                
                # Create candidate with entities (no calculation - just pass data)
                candidate = AllocationCandidate(
                    field=field,
                    crop=crop,
                    start_date=candidate_period.start_date,
                    completion_date=candidate_period.completion_date,
                    growth_days=candidate_period.growth_days,
                    accumulated_gdd=0.0,
                    area_used=area_used,
                )
                
                # ===== LEGACY FILTERING - DO NOT REPLICATE =====
                # See _generate_candidates() for detailed warning.
                if config.enable_candidate_filtering:
                    # Get baseline metrics (no context - this is pre-allocation filtering)
                    baseline_metrics = candidate.get_metrics()
                    cost = baseline_metrics.cost
                    profit = baseline_metrics.profit
                    revenue = baseline_metrics.revenue
                    profit_rate = (profit / cost) if cost > 0 else 0.0
                    
                    if profit_rate < config.min_profit_rate_threshold:
                        continue
                    if revenue is not None and cost > 0:
                        if revenue / cost < config.min_revenue_cost_ratio:
                            continue
                    if request.optimization_objective == "maximize_profit" and profit < 0:
                        continue  # Skip unprofitable candidates
                
                candidates.append(candidate)
        
        return candidates
    
    def _post_filter_candidates(
        self,
        candidates: List[AllocationCandidate],
        config: OptimizationConfig,
    ) -> List[AllocationCandidate]:
        """Post-filter candidates to keep only top K per field×crop.
        
        This prevents candidate explosion while keeping high-quality options.
        """
        
        # Group candidates by field×crop
        candidates_by_field_crop = {}
        for c in candidates:
            key = (c.field.field_id, c.crop.crop_id)
            if key not in candidates_by_field_crop:
                candidates_by_field_crop[key] = []
            candidates_by_field_crop[key].append(c)
        
        # Sort each group by profit_rate and keep top K
        filtered_candidates = []
        for key, cands in candidates_by_field_crop.items():
            sorted_cands = sorted(cands, key=lambda c: c.profit_rate, reverse=True)
            filtered_candidates.extend(sorted_cands[:config.max_candidates_per_field_crop])
        
        return filtered_candidates

    
    def _greedy_allocation(
        self,
        candidates: List[AllocationCandidate],
        crops: List,
        optimization_objective: str,
        planning_start_date,
    ) -> List[CropAllocation]:
        """Select allocations using greedy allocation with dynamic re-sorting.
        
        Strategy: For each selection, re-evaluate remaining candidates with current
        interaction rules and select the best one. This ensures continuous cultivation
        penalties are properly considered.
        
        Applies interaction rules (continuous cultivation) to adjust revenue dynamically.
        
        Note: optimization_objective parameter is kept for backward compatibility
        but the actual optimization uses the unified objective (profit maximization).
        """
        # Track allocated resources
        field_schedules: Dict[str, List[CropAllocation]] = {}  # field_id -> allocations
        crop_areas: Dict[str, float] = {c.crop.crop_id: 0.0 for c in crops}
        # Note: No need to manually track crop_revenues!
        # OptimizationMetrics.calculate_crop_cumulative_revenue() handles this (single source of truth)
        
        # Greedily select allocations with dynamic re-sorting
        allocations = []
        remaining_candidates = candidates.copy()
        
        while remaining_candidates:
            # Evaluate all remaining candidates with current state
            # get_metrics() will automatically calculate:
            # - cumulative revenue (market demand tracking)
            # - interaction impact (continuous cultivation, rotation, etc.)
            # This is the SINGLE SOURCE OF TRUTH for all profit calculations
            
            # Sort by profit with current context
            # Pass allocations, field_schedules, interaction_rules, and planning_start_date
            remaining_candidates.sort(
                key=lambda x: self._get_candidate_sort_key_with_full_context(
                    x, allocations, field_schedules, self.interaction_rule_service.rules, planning_start_date
                ),
                reverse=True
            )
            
            # Try to allocate the best candidates
            allocated = False
            for candidate in remaining_candidates:
                # Check time overlap with existing allocations in the same field
                field_id = candidate.field.field_id
                if field_id not in field_schedules:
                    field_schedules[field_id] = []
                
                has_overlap = False
                for existing in field_schedules[field_id]:
                    # Use overlaps_with_fallow to respect fallow period constraint
                    # Call from candidate (AllocationCandidate) to use the flexible method
                    if candidate.overlaps_with_fallow(existing):
                        has_overlap = True
                        break
                
                if has_overlap:
                    continue  # Skip this candidate
                
                # Found a feasible candidate - allocate it
                # All calculations (market demand, interaction impact) handled by get_metrics()
                crop_id = candidate.crop.crop_id
                # Convert candidate to allocation with full context
                allocation = self._candidate_to_allocation(
                    candidate, allocations, field_schedules, self.interaction_rule_service.rules, planning_start_date
                )
                allocations.append(allocation)
                field_schedules[field_id].append(allocation)
                crop_areas[crop_id] += allocation.area_used
                
                # No need to manually update crop_revenues or interaction_impact!
                # Next iteration will automatically calculate them
                
                remaining_candidates.remove(candidate)
                allocated = True
                break
            
            # If no candidate could be allocated, stop
            if not allocated:
                break
        
        return allocations
    
    def _get_candidate_sort_key_with_full_context(
        self, 
        candidate: AllocationCandidate, 
        current_allocations: List[CropAllocation],
        field_schedules: Dict[str, List[CropAllocation]],
        interaction_rules: List,
        planning_start_date
    ) -> float:
        """Get sort key for a candidate with full context.
        
        This calculates profit rate considering:
        - Market demand limits (from current_allocations)
        - Interaction rules (from field_schedules)
        
        All calculations delegated to OptimizationMetrics (single source of truth).
        
        Args:
            candidate: Candidate to evaluate
            current_allocations: Currently selected allocations
            field_schedules: Dict mapping field_id to allocations
            interaction_rules: List of interaction rules
            planning_start_date: Planning period start date
            
        Returns:
            Profit rate (to be maximized)
        """
        # Use factory directly (single source of truth)
        metrics = OptimizationMetrics.create_for_allocation(
            area_used=candidate.area_used,
            revenue_per_area=candidate.crop.revenue_per_area,
            max_revenue=candidate.crop.max_revenue,
            growth_days=candidate.growth_days,
            daily_fixed_cost=candidate.field.daily_fixed_cost,
            crop_id=candidate.crop.crop_id,
            crop=candidate.crop,
            field=candidate.field,
            start_date=candidate.start_date,
            current_allocations=current_allocations,
            field_schedules=field_schedules,
            interaction_rules=interaction_rules,
            planning_start_date=planning_start_date,
        )
        cost = metrics.cost
        if cost > 0:
            return metrics.profit / cost
        return 0.0
    
    def _weighted_interval_scheduling_dp_with_profits(
        self,
        candidates: List[AllocationCandidate],
        candidate_profits: Dict[int, float],
    ) -> List[AllocationCandidate]:
        """Solve weighted interval scheduling with externally provided profit values.
        
        This variant accepts pre-calculated profit values that consider:
        - Market demand limits (cumulative revenue across fields)
        - Interaction rules (continuous cultivation, rotation, etc.)
        
        Args:
            candidates: List of allocation candidates for a single field
            candidate_profits: Dict mapping id(candidate) to evaluated profit
            
        Returns:
            Optimal subset of candidates
        """
        if not candidates:
            return []
        
        # Sort by completion date
        sorted_candidates = sorted(candidates, key=lambda c: c.completion_date)
        n = len(sorted_candidates)
        
        # dp[i] = maximum profit considering candidates 0..i-1
        dp = [0.0] * (n + 1)
        
        # For each candidate, find the latest non-overlapping candidate
        p = [0] * n
        for i in range(n):
            p[i] = self._find_latest_non_overlapping(sorted_candidates, i)
        
        # DP: compute maximum profit using provided profit values
        for i in range(1, n + 1):
            candidate = sorted_candidates[i - 1]
            # Use externally provided profit (considers full context)
            profit = candidate_profits.get(id(candidate), 0.0)
            
            # Option 1: Don't include candidate i-1
            without_i = dp[i - 1]
            # Option 2: Include candidate i-1
            with_i = profit + dp[p[i - 1]]
            
            dp[i] = max(without_i, with_i)
        
        # Reconstruct solution
        selected = []
        i = n
        while i > 0:
            candidate = sorted_candidates[i - 1]
            profit = candidate_profits.get(id(candidate), 0.0)
            
            # Check if candidate i-1 was included
            without_i = dp[i - 1]
            with_i = profit + dp[p[i - 1]]
            
            if with_i >= without_i:  # Candidate was included
                selected.append(candidate)
                i = p[i - 1]
            else:
                i -= 1
        
        return list(reversed(selected))
    
    def _weighted_interval_scheduling_dp(
        self,
        candidates: List[AllocationCandidate],
    ) -> List[AllocationCandidate]:
        """Solve weighted interval scheduling problem for a single field using DP.
        
        This is the classic weighted interval scheduling problem:
        - Given a set of intervals (cultivation periods) with weights (profit)
        - Find the maximum weight subset with no overlapping intervals
        
        Algorithm:
        1. Sort candidates by completion_date
        2. For each candidate i, compute:
           - dp[i] = max profit using candidates 0..i
           - dp[i] = max(dp[i-1], profit[i] + dp[p(i)])
           - p(i) = latest candidate that doesn't overlap with i
        3. Reconstruct solution by backtracking
        
        Time Complexity: O(n log n) for sorting + O(n log n) for DP = O(n log n)
        Space Complexity: O(n)
        
        Args:
            candidates: List of allocation candidates for a single field
            
        Returns:
            Optimal subset of candidates (no time overlaps, maximum profit)
        """
        if not candidates:
            return []
        
        # Sort by completion date
        sorted_candidates = sorted(candidates, key=lambda c: c.completion_date)
        n = len(sorted_candidates)
        
        # dp[i] = maximum profit considering candidates 0..i-1
        dp = [0.0] * (n + 1)
        
        # For each candidate, find the latest non-overlapping candidate
        # p[i] = index of latest candidate that doesn't overlap with i
        p = [0] * n
        for i in range(n):
            # Binary search for latest non-overlapping candidate
            p[i] = self._find_latest_non_overlapping(sorted_candidates, i)
        
        # DP: compute maximum profit
        for i in range(1, n + 1):
            candidate = sorted_candidates[i - 1]
            # Option 1: Don't include candidate i-1
            without_i = dp[i - 1]
            # Option 2: Include candidate i-1
            with_i = candidate.profit + dp[p[i - 1]]
            
            dp[i] = max(without_i, with_i)
        
        # Reconstruct solution
        selected = []
        i = n
        while i > 0:
            candidate = sorted_candidates[i - 1]
            # Check if candidate i-1 was included
            without_i = dp[i - 1]
            with_i = candidate.profit + dp[p[i - 1]]
            
            if with_i >= without_i:  # Candidate was included
                selected.append(candidate)
                i = p[i - 1]
            else:
                i -= 1
        
        return selected
    
    def _find_latest_non_overlapping(
        self,
        sorted_candidates: List[AllocationCandidate],
        i: int,
    ) -> int:
        """Find the latest candidate that doesn't overlap with candidate i (including fallow period).
        
        Uses binary search to find the rightmost candidate j such that
        sorted_candidates[j] doesn't overlap with sorted_candidates[i] when considering fallow periods.
        
        CRITICAL: This method now considers fallow periods to ensure proper soil recovery time.
        Two candidates don't overlap if: completion_date + fallow_period_days <= next_start_date
        
        Example:
            If candidate A completes on June 30 with 28-day fallow period,
            candidate B can only start on July 28 or later.
            
        Note: We use the field's fallow_period_days for proper constraint enforcement.
        
        Args:
            sorted_candidates: Candidates sorted by completion_date
            i: Index of current candidate
            
        Returns:
            Index + 1 for dp array (0 means no non-overlapping candidate)
        """
        from datetime import timedelta
        
        current_candidate = sorted_candidates[i]
        
        # Binary search for rightmost candidate that doesn't overlap with fallow period
        left, right = 0, i - 1
        result = 0
        
        while left <= right:
            mid = (left + right) // 2
            candidate = sorted_candidates[mid]
            
            # Check if candidate doesn't overlap considering fallow period
            # candidate ends (with fallow) before current starts
            candidate_end_with_fallow = candidate.completion_date + timedelta(
                days=candidate.field.fallow_period_days
            )
            
            if candidate_end_with_fallow <= current_candidate.start_date:
                result = mid + 1  # +1 for dp array indexing
                left = mid + 1
            else:
                right = mid - 1
        
        return result
    
    def _dp_allocation(
        self,
        candidates: List[AllocationCandidate],
        crops: List,
        fields: List[Field],
        planning_start_date,
    ) -> List[CropAllocation]:
        """Allocate crops using sequential per-field DP with cumulative context.
        
        Algorithm (CORRECTED):
        1. Group candidates by field
        2. For each field SEQUENTIALLY:
           a. Re-evaluate candidates with current allocation context (market demand, interaction)
           b. Solve weighted interval scheduling DP with updated profit values
           c. Add selected allocations to global solution
        3. Return optimized solution
        
        Key Fix: Fields are processed sequentially, not independently.
        Each field's DP considers what has already been allocated in previous fields.
        This prevents all fields from choosing the same crop when market demand is limited.
        
        Args:
            candidates: All allocation candidates
            crops: List of crop aggregates
            fields: List of fields
            
        Returns:
            List of selected allocations
        """
        # Group candidates by field
        candidates_by_field = {}
        for candidate in candidates:
            field_id = candidate.field.field_id
            if field_id not in candidates_by_field:
                candidates_by_field[field_id] = []
            candidates_by_field[field_id].append(candidate)
        
        # Solve DP for each field SEQUENTIALLY (considering previous allocations)
        allocations = []
        field_schedules = {}
        
        for field in fields:
            field_id = field.field_id
            field_candidates = candidates_by_field.get(field_id, [])
            
            if not field_candidates:
                continue
            
            # Re-evaluate candidates with current allocation context
            # This updates profit values to reflect:
            # - Market demand already consumed by previous fields
            # - Interaction impact from previous allocations in this field
            # - Soil recovery bonus from fallow periods
            candidate_profits = {}
            for candidate in field_candidates:
                # Use factory directly (single source of truth)
                metrics = OptimizationMetrics.create_for_allocation(
                    area_used=candidate.area_used,
                    revenue_per_area=candidate.crop.revenue_per_area,
                    max_revenue=candidate.crop.max_revenue,
                    growth_days=candidate.growth_days,
                    daily_fixed_cost=candidate.field.daily_fixed_cost,
                    crop_id=candidate.crop.crop_id,
                    crop=candidate.crop,
                    field=candidate.field,
                    start_date=candidate.start_date,
                    current_allocations=allocations,
                    field_schedules=field_schedules,
                    interaction_rules=self.interaction_rule_service.rules,
                    planning_start_date=planning_start_date,
                )
                # Store evaluated profit for this candidate
                candidate_profits[id(candidate)] = metrics.profit
            
            # Solve weighted interval scheduling with evaluated profits
            selected_candidates = self._weighted_interval_scheduling_dp_with_profits(
                field_candidates, candidate_profits
            )
            
            # Convert to CropAllocation
            for candidate in selected_candidates:
                # Convert with current context for correct revenue calculation
                allocation = self._candidate_to_allocation(
                    candidate, allocations, field_schedules, self.interaction_rule_service.rules, planning_start_date
                )
                allocations.append(allocation)
                
                # Update field schedules
                if field_id not in field_schedules:
                    field_schedules[field_id] = []
                field_schedules[field_id].append(allocation)
        
        return allocations
    
    def _local_search(
        self,
        initial_solution: List[CropAllocation],
        candidates: List[AllocationCandidate],
        fields: List[Field],
        config: OptimizationConfig,
        time_limit: Optional[float] = None,
        planning_start_date = None,
    ) -> List[CropAllocation]:
        """Improve solution using Local Search or ALNS.
        
        Automatically selects algorithm based on config.enable_alns:
        - False: Hill Climbing (small neighborhoods, fast)
        - True: ALNS (large neighborhoods, higher quality)
        
        Uses unified optimization objective (profit maximization).
        """
        # Skip if initial solution is too small
        if len(initial_solution) < 2:
            return initial_solution
        
        # Extract unique crops from candidates
        crops_dict = {}
        for c in candidates:
            if c.crop.crop_id not in crops_dict:
                crops_dict[c.crop.crop_id] = c.crop
        crops_list = list(crops_dict.values())
        
        # Choose algorithm based on config
        if config.enable_alns:
            # Use ALNS
            if self.alns_optimizer is None:
                self.alns_optimizer = ALNSOptimizer(config)
            
            return self.alns_optimizer.optimize(
                initial_solution=initial_solution,
                candidates=candidates,
                fields=fields,
                crops=crops_list,
                max_iterations=config.alns_iterations,
            )
        else:
            # Use Hill Climbing (existing implementation)
            return self._hill_climbing_local_search(
                initial_solution, candidates, fields, config, time_limit, planning_start_date
            )
    
    def _hill_climbing_local_search(
        self,
        initial_solution: List[CropAllocation],
        candidates: List[AllocationCandidate],
        fields: List[Field],
        config: OptimizationConfig,
        time_limit: Optional[float] = None,
        planning_start_date = None,
    ) -> List[CropAllocation]:
        """Hill Climbing local search implementation.
        
        Phase 1: Neighbor sampling to limit computational cost
        Phase 2: Incremental feasibility checking for faster validation
        Phase 3: Adaptive early stopping
        """
        start_time = time.time()
        current_solution = initial_solution
        current_profit = self._calculate_total_profit(current_solution)
        
        no_improvement_count = 0
        best_profit_so_far = current_profit
        consecutive_near_optimal = 0
        
        # Extract unique crops
        crops_dict = {}
        for c in candidates:
            if c.crop.crop_id not in crops_dict:
                crops_dict[c.crop.crop_id] = c.crop
        crops_list = list(crops_dict.values())
        
        # Phase 3: Adaptive parameters
        problem_size = len(initial_solution)
        max_no_improvement = max(10, min(config.max_no_improvement, problem_size // 2)) if config.enable_adaptive_early_stopping else config.max_no_improvement
        improvement_threshold = current_profit * config.improvement_threshold_ratio if config.enable_adaptive_early_stopping else 0
        
        for iteration in range(config.max_local_search_iterations):
            # Check time limit
            if time_limit and (time.time() - start_time) > time_limit:
                break
            
            # Generate neighbors using NeighborGeneratorService (Phase 1 refactoring)
            neighbors = self.neighbor_generator.generate_neighbors(
                solution=current_solution,
                candidates=candidates,
                fields=fields,
                crops=crops_list,
            )
            
            # Find best neighbor
            best_neighbor = None
            best_profit = current_profit
            
            for neighbor in neighbors:
                # Build field_schedules from neighbor for interaction rule calculation
                neighbor_field_schedules = {}
                for alloc in neighbor:
                    field_id = alloc.field.field_id
                    if field_id not in neighbor_field_schedules:
                        neighbor_field_schedules[field_id] = []
                    neighbor_field_schedules[field_id].append(alloc)
                
                # Recalculate revenue with full context
                # Delegate to OptimizationMetrics (single source of truth)
                adjusted_neighbor = OptimizationMetrics.recalculate_allocations_with_context(
                    neighbor, 
                    neighbor_field_schedules, 
                    self.interaction_rule_service.rules,
                    planning_start_date
                )
                
                # Use standard or incremental feasibility check
                if self._is_feasible_solution(adjusted_neighbor):
                    neighbor_profit = self._calculate_total_profit(adjusted_neighbor)
                    if neighbor_profit > best_profit:
                        best_neighbor = adjusted_neighbor
                        best_profit = neighbor_profit
            
            # Update if improvement found
            if best_neighbor is not None:
                improvement = best_profit - current_profit
                
                # Phase 3: Check if improvement is significant
                if config.enable_adaptive_early_stopping:
                    if improvement > improvement_threshold:
                        current_solution = best_neighbor
                        current_profit = best_profit
                        no_improvement_count = 0
                        best_profit_so_far = best_profit
                    else:
                        # Improvement too small
                        no_improvement_count += 1
                else:
                    current_solution = best_neighbor
                    current_profit = best_profit
                    no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            # Phase 3: Convergence check
            if config.enable_adaptive_early_stopping:
                if current_profit >= best_profit_so_far * 0.999:  # Within 0.1%
                    consecutive_near_optimal += 1
                    if consecutive_near_optimal >= 5:
                        break  # Converged
                else:
                    consecutive_near_optimal = 0
            
            # Early stopping
            if no_improvement_count >= max_no_improvement:
                break
        
        return current_solution
    
    # ===== Helper Methods =====
    
    def _candidate_to_allocation(
        self, 
        candidate: AllocationCandidate, 
        current_allocations: Optional[List[CropAllocation]] = None,
        field_schedules: Optional[Dict[str, List[CropAllocation]]] = None,
        interaction_rules: Optional[List] = None,
        planning_start_date = None
    ) -> CropAllocation:
        """Convert AllocationCandidate to CropAllocation.
        
        All calculations delegated to OptimizationMetrics (single source of truth).
        
        Args:
            candidate: Candidate to convert
            current_allocations: Currently selected allocations (for market demand tracking)
            field_schedules: Dict mapping field_id to allocations (for interaction rules)
            interaction_rules: List of interaction rules
            planning_start_date: Planning period start date (for soil recovery calculation)
            
        Returns:
            CropAllocation with correct revenue/profit calculated from full context
        """
        # Use factory directly (single source of truth)
        metrics = OptimizationMetrics.create_for_allocation(
            area_used=candidate.area_used,
            revenue_per_area=candidate.crop.revenue_per_area,
            max_revenue=candidate.crop.max_revenue,
            growth_days=candidate.growth_days,
            daily_fixed_cost=candidate.field.daily_fixed_cost,
            crop_id=candidate.crop.crop_id,
            crop=candidate.crop,
            field=candidate.field,
            start_date=candidate.start_date,
            current_allocations=current_allocations,
            field_schedules=field_schedules,
            interaction_rules=interaction_rules,
            planning_start_date=planning_start_date,
        )
        
        return CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=candidate.field,
            crop=candidate.crop,
            area_used=candidate.area_used,
            start_date=candidate.start_date,
            completion_date=candidate.completion_date,
            growth_days=candidate.growth_days,
            accumulated_gdd=candidate.accumulated_gdd,
            total_cost=metrics.cost,
            expected_revenue=metrics.revenue,
            profit=metrics.profit,
        )

    def _calculate_total_profit(self, allocations: List[CropAllocation]) -> float:
        """Calculate total profit of a solution."""
        return sum(alloc.profit for alloc in allocations if alloc.profit is not None)

    def _is_feasible_solution(self, allocations: List[CropAllocation]) -> bool:
        """Check if solution is valid.
        
        Checks:
        1. No time overlaps within each field
        2. Revenue calculations are consistent with market demand limits
        
        Note on market demand:
        - Exceeding market demand is NOT a violation (planting is allowed)
        - Revenue should already be 0 for allocations beyond market capacity
        - This check detects calculation errors, not policy violations
        - If total_revenue > max_revenue, it means revenue wasn't properly
          recalculated with cumulative context (a bug, not a constraint violation)
        """
        # Check for time overlaps within each field
        field_allocations: Dict[str, List[CropAllocation]] = {}
        for alloc in allocations:
            field_id = alloc.field.field_id
            if field_id not in field_allocations:
                field_allocations[field_id] = []
            field_allocations[field_id].append(alloc)
        
        for field_id, field_allocs in field_allocations.items():
            for i, alloc1 in enumerate(field_allocs):
                for alloc2 in field_allocs[i+1:]:
                    if alloc1.overlaps_with_fallow(alloc2):
                        return False  # Overlap found (considering fallow period)
        
        # Verify revenue calculations are consistent (sanity check for bugs)
        # Get unique crops
        unique_crops = {}
        for alloc in allocations:
            unique_crops[alloc.crop.crop_id] = alloc.crop
        
        # Check: if cumulative revenue > max_revenue, revenue calculation has a bug
        for crop_id, crop in unique_crops.items():
            if crop.max_revenue is not None:
                # Use unified calculation method
                total_revenue = OptimizationMetrics.calculate_crop_cumulative_revenue(
                    crop_id, allocations
                )
                # This should never happen if OptimizationMetrics works correctly
                # Allow small tolerance for floating point errors
                if total_revenue > crop.max_revenue * 1.001:  # 0.1% tolerance
                    return False  # Bug detected: revenue not properly capped
        
        return True

    def _build_result(
        self,
        allocations: List[CropAllocation],
        fields: List[Field],
        computation_time: float,
        algorithm_used: str,
    ) -> MultiFieldOptimizationResult:
        """Build final optimization result."""
        # Group allocations by field
        field_allocations: Dict[str, List[CropAllocation]] = {f.field_id: [] for f in fields}
        for alloc in allocations:
            field_allocations[alloc.field.field_id].append(alloc)
        
        # Build field schedules
        field_schedules = []
        total_cost = 0.0
        total_revenue = 0.0
        total_profit = 0.0
        crop_areas: Dict[str, float] = {}
        
        for field in fields:
            field_allocs = field_allocations[field.field_id]
            
            # Calculate field totals
            field_cost = sum(a.total_cost for a in field_allocs)
            field_revenue = sum(a.expected_revenue for a in field_allocs if a.expected_revenue is not None)
            field_profit = sum(a.profit for a in field_allocs if a.profit is not None)
            field_area_used = sum(a.area_used for a in field_allocs)
            field_utilization = (field_area_used / field.area * 100) if field.area > 0 else 0.0
            
            field_schedule = FieldSchedule(
                field=field,
                allocations=field_allocs,
                total_area_used=field_area_used,
                total_cost=field_cost,
                total_revenue=field_revenue,
                total_profit=field_profit,
                utilization_rate=field_utilization,
            )
            field_schedules.append(field_schedule)
            
            total_cost += field_cost
            total_revenue += field_revenue
            total_profit += field_profit
            
            # Aggregate crop areas
            for alloc in field_allocs:
                crop_id = alloc.crop.crop_id
                crop_areas[crop_id] = crop_areas.get(crop_id, 0.0) + alloc.area_used
        
        return MultiFieldOptimizationResult(
            optimization_id=str(uuid.uuid4()),
            field_schedules=field_schedules,
            total_cost=total_cost,
            total_revenue=total_revenue,
            total_profit=total_profit,
            crop_areas=crop_areas,
            optimization_time=computation_time,
            algorithm_used=algorithm_used,
            is_optimal=False,  # Greedy + LS doesn't guarantee optimality
        )
