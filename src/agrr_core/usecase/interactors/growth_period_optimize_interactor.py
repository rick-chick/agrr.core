"""Optimal growth period calculation interactor.

This interactor finds the optimal cultivation start date that maximizes profit
(or minimizes cost when revenue is unknown) based on daily fixed costs,
while ensuring completion by a specified deadline.

The optimization follows this logic:
1. Generate candidate start dates from earliest_start_date to completion_deadline
2. For each candidate, calculate cultivation progress until 100% completion
3. Filter out candidates that cannot complete by the deadline
4. Calculate total cost = growth_days * daily_fixed_cost for valid candidates
5. Select the candidate with maximum profit (minimum cost if revenue unknown)

The evaluation period has dual meaning:
- evaluation_period_start: Earliest possible cultivation start date
- evaluation_period_end: Completion deadline (cultivation must finish by this date)
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from collections import defaultdict

from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    OptimalGrowthPeriodResponseDTO,
    CandidateResultDTO,
)
from agrr_core.usecase.dto.growth_progress_calculate_request_dto import (
    GrowthProgressCalculateRequestDTO,
)
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.optimization_result_gateway import (
    OptimizationResultGateway,
)
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.usecase.interactors.growth_progress_calculate_interactor import (
    GrowthProgressCalculateInteractor,
)
from agrr_core.usecase.ports.input.growth_period_optimize_input_port import (
    GrowthPeriodOptimizeInputPort,
)
from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.value_objects.yield_impact_accumulator import (
    YieldImpactAccumulator,
)
from agrr_core.usecase.interactors.base_optimizer import BaseOptimizer
from agrr_core.usecase.gateways.weather_interpolator import WeatherInterpolator
import os
import time

class GrowthPeriodOptimizeInteractor(
    BaseOptimizer[CandidateResultDTO],
    GrowthPeriodOptimizeInputPort
):
    """Interactor for finding optimal growth period using unified objective."""

    def __init__(
        self,
        crop_profile_gateway: CropProfileGateway,
        weather_gateway: WeatherGateway,
        optimization_result_gateway: OptimizationResultGateway = None,
        interaction_rule_gateway: InteractionRuleGateway = None,
        weather_interpolator: Optional[WeatherInterpolator] = None,
    ):
        super().__init__()  # Initialize BaseOptimizer
        self.crop_profile_gateway = crop_profile_gateway
        self.weather_gateway = weather_gateway
        self.optimization_result_gateway = optimization_result_gateway
        self.interaction_rule_gateway = interaction_rule_gateway
        self.weather_interpolator = weather_interpolator
        
        # Use existing growth progress calculator
        self.growth_progress_interactor = GrowthProgressCalculateInteractor(
            crop_profile_gateway=crop_profile_gateway,
            weather_gateway=weather_gateway,
        )

    def execute(
        self, request: OptimalGrowthPeriodRequestDTO
    ) -> OptimalGrowthPeriodResponseDTO:
        """Calculate optimal growth period using efficient sliding window algorithm.

        Args:
            request: Request DTO containing crop info, evaluation period, and field

        Returns:
            Response DTO containing optimal period and all candidate evaluations
            
        Raises:
            ValueError: If no candidate reaches 100% growth completion
        """
        # Load interaction rules via gateway (if gateway is configured with file path)
        interaction_rules = []
        if self.interaction_rule_gateway:
            try:
                interaction_rules = self.interaction_rule_gateway.get_rules()
            except (ValueError, Exception):
                # Gateway not configured with file path or file not found - no rules to apply
                pass
        
        # Get daily_fixed_cost from field entity
        daily_fixed_cost = request.field.daily_fixed_cost
        
        # Get crop profile for revenue information
        crop_profile = self._get_crop_profile(
            request.crop_id, request.variety
        )
        
        # Use efficient sliding window algorithm
        candidates = self._evaluate_candidates_efficient(request, daily_fixed_cost, crop_profile.crop)
        
        # Find optimal candidate (maximum profit, excluding failures and deadline violations)
        valid_candidates = [c for c in candidates if c.total_cost is not None]
        
        # Optionally filter to keep only the shortest cultivation period per completion date
        # This removes redundant candidates: if multiple start dates reach the same completion date,
        # we only keep the one with shortest growth_days (lowest cost, latest start)
        if request.filter_redundant_candidates:
            valid_candidates = self._filter_shortest_candidates_per_completion_date(valid_candidates)
        
        if not valid_candidates:
            # Calculate total required GDD for better error message
            total_required_gdd = sum(
                sr.thermal.required_gdd 
                for sr in crop_profile.stage_requirements
            )
            
            # Check if any candidate completed but exceeded deadline
            completed_candidates = [c for c in candidates if c.completion_date is not None]
            if completed_candidates:
                earliest_completion = min(c.completion_date for c in completed_candidates)
                # Only show earliest completion if it's within a reasonable range (not due to bug)
                if earliest_completion <= request.evaluation_period_end + timedelta(days=365):
                    raise ValueError(
                        f"No candidate can complete by the deadline ({request.evaluation_period_end.date()}). "
                        f"Earliest possible completion is {earliest_completion.date()}. "
                        f"Consider extending the deadline or choosing an earlier start date range."
                    )
            
            # Default error message
            raise ValueError(
                f"No candidate can complete growth within the planning period. "
                f"Total required GDD: {total_required_gdd:.1f}. "
                f"Planning period: {request.evaluation_period_start.date()} to {request.evaluation_period_end.date()}. "
                f"Consider extending the deadline, reducing GDD requirements, or choosing different start dates."
            )
        
        # Use BaseOptimizer's select_best (unified objective function)
        optimal_candidate = self.select_best(valid_candidates)
        
        # Mark optimal candidate in the filtered list
        for candidate in valid_candidates:
            if candidate.start_date == optimal_candidate.start_date:
                # Create new candidate with is_optimal=True
                object.__setattr__(candidate, 'is_optimal', True)
        
        # Calculate revenue and profit for optimal candidate
        optimal_metrics = optimal_candidate.get_metrics()
        
        return OptimalGrowthPeriodResponseDTO(
            crop_name=crop_profile.crop.name,
            variety=crop_profile.crop.variety,
            optimal_start_date=optimal_candidate.start_date,
            completion_date=optimal_candidate.completion_date,
            growth_days=optimal_candidate.growth_days,
            total_cost=optimal_candidate.total_cost,
            revenue=optimal_metrics.revenue,
            profit=optimal_metrics.profit,
            daily_fixed_cost=daily_fixed_cost,
            field=request.field,
            candidates=valid_candidates,  # Use filtered candidates (no redundant completion dates)
        )

    def _evaluate_candidates_efficient(
        self, request: OptimalGrowthPeriodRequestDTO, daily_fixed_cost: float, crop: Crop
    ) -> List[CandidateResultDTO]:
        """Evaluate candidates using efficient sliding window algorithm.
        
        This method uses a sliding window approach to minimize redundant calculations:
        1. Calculate completion for first start date
        2. Slide start date forward, subtracting removed days and adding new days as needed
        3. Check if completion date exceeds deadline
        
        Time complexity: O(M) where M is weather data length
        vs. naive O(N×M) where N is number of candidates
        
        Args:
            request: Request DTO with evaluation parameters
            
        Returns:
            List of candidate results
        """
        prof = os.getenv("AGRR_PROFILE") == "1"
        t_all0 = time.perf_counter() if prof else 0.0

        # Get crop requirements via gateway
        crop_profile = self.crop_profile_gateway.get()
        
        # Get weather data via gateway (file path configured at initialization)
        t_w0 = time.perf_counter() if prof else 0.0
        weather_data = self.weather_gateway.get()
        if prof:
            t_w1 = time.perf_counter()
            print(f"[PROFILE] GrowthPeriod: weather_get count={len(weather_data)} elapsed={t_w1-t_w0:.3f}s", flush=True)
        
        # Calculate total required GDD
        total_required_gdd = sum(
            stage_req.thermal.required_gdd 
            for stage_req in crop_profile.stage_requirements
        )
        
        # Stage requirements (for stage-aware GDD accumulation)
        stage_requirements = crop_profile.stage_requirements
        
        # Create weather data lookup by date
        weather_by_date = {w.time.date(): w for w in weather_data}
        
        # Sort dates to ensure chronological order
        sorted_dates = sorted(weather_by_date.keys())
        
        # Apply interpolation if interpolator is provided
        if self.weather_interpolator:
            weather_by_date = self.weather_interpolator.interpolate_temperature(
                weather_by_date, sorted_dates
            )
        
        if not sorted_dates:
            raise ValueError("No weather data available")
        
        # Initialize for first candidate (evaluation_period_start)
        start_date = request.evaluation_period_start
        current_start = start_date
        accumulated_gdd = 0.0
        window_start_idx = 0
        window_end_idx = 0
        
        results = []
        gdd_per_candidate = []  # Track accumulated GDD for each candidate
        
        # Initial scan removed in favor of stage-aware computation path
        t_init0 = time.perf_counter() if prof else 0.0
        
        # Early-stop fast path: compute completion from current_start using stage-aware accumulation
        if request.early_stop_at_first:
            comp = self._compute_completion_from_start(
                start=current_start,
                weather_by_date=weather_by_date,
                sorted_dates=sorted_dates,
                stage_requirements=stage_requirements,
            )
            if comp is not None:
                completion_date, growth_days, yield_factor = comp
                if completion_date <= request.evaluation_period_end:
                    results.append(CandidateResultDTO(
                        start_date=current_start,
                        completion_date=completion_date,
                        growth_days=growth_days,
                        field=request.field,
                        crop=crop,
                        is_optimal=False,
                        yield_factor=yield_factor,
                    ))
            # Short-circuit return (only evaluate first start date)
            return results
        
        # Slide window: move start date forward one day at a time
        if prof:
            t_init1 = time.perf_counter()
            print(f"[PROFILE] GrowthPeriod: initial_scan elapsed={t_init1-t_init0:.3f}s", flush=True)
        t_slide0 = time.perf_counter() if prof else 0.0
        while current_start < request.evaluation_period_end:
            # Move start date forward
            prev_start = current_start
            current_start += timedelta(days=1)
            
            # For multi-stage with different temperature profiles, exact sliding-window subtraction
            # is non-trivial. Use stage-aware recomputation from current_start to completion.
            comp = self._compute_completion_from_start(
                start=current_start,
                weather_by_date=weather_by_date,
                sorted_dates=sorted_dates,
                stage_requirements=stage_requirements,
            )
            
            # Check if this candidate is valid
            if comp is None:
                break
            completion_date, growth_days, yield_factor = comp
            if completion_date <= request.evaluation_period_end:
                results.append(CandidateResultDTO(
                    start_date=current_start,
                    completion_date=completion_date,
                    growth_days=growth_days,
                    field=request.field,
                    crop=crop,
                    is_optimal=False,
                    yield_factor=yield_factor,
                ))
                # Early-stop option: stop sliding once a valid candidate is found
                if request.early_stop_at_first:
                    break
            else:
                # Completion exceeds deadline - stop here
                break
        
        if prof:
            t_slide1 = time.perf_counter()
            print(f"[PROFILE] GrowthPeriod: sliding_window elapsed={t_slide1-t_slide0:.3f}s candidates={len(results)}", flush=True)

        # Save intermediate results if gateway is available
        if self.optimization_result_gateway:
            intermediate_results = []
            for idx, candidate in enumerate(results):
                intermediate_result = OptimizationIntermediateResult(
                    start_date=candidate.start_date,
                    completion_date=candidate.completion_date,
                    growth_days=candidate.growth_days,
                    accumulated_gdd=gdd_per_candidate[idx] if idx < len(gdd_per_candidate) else 0.0,
                    field=candidate.field,
                    is_optimal=candidate.is_optimal,
                    base_temperature=temperature_profile.base_temperature,
                )
                intermediate_results.append(intermediate_result)
            
            # Generate optimization ID from request parameters
            optimization_id = f"{request.crop_id}_{request.variety or 'default'}_{request.evaluation_period_start.date()}_{request.evaluation_period_end.date()}"
            self.optimization_result_gateway.save(optimization_id, intermediate_results)
        
        # Sort candidates by cost (ascending: lower cost is better)
        # Valid candidates (with cost) come first, sorted by cost
        # Invalid candidates (without cost) come last, maintaining chronological order
        valid_results = [r for r in results if r.total_cost is not None]
        invalid_results = [r for r in results if r.total_cost is None]
        
        # Sort valid candidates by cost (ascending)
        valid_results.sort(key=lambda r: r.total_cost)
        
        # Return sorted valid candidates followed by invalid candidates
        out = valid_results + invalid_results
        if prof:
            t_all1 = time.perf_counter()
            print(f"[PROFILE] GrowthPeriod: total elapsed={t_all1-t_all0:.3f}s out_candidates={len(out)}", flush=True)
        return out

    def _compute_completion_from_start(self, start, weather_by_date, sorted_dates, stage_requirements):
        """Compute completion date using stage-aware GDD accumulation from a start date.

        Returns tuple (completion_date, growth_days, yield_factor) or None if cannot complete.
        """
        from datetime import datetime, timedelta
        # Initialize per-stage remaining requirements
        remaining = [sr.thermal.required_gdd for sr in stage_requirements]
        if not remaining:
            return None
        stage_idx = 0
        completion_date = None
        # Iterate forward from start across available weather
        idx = 0
        # Find starting index in sorted_dates
        while idx < len(sorted_dates) and datetime.combine(sorted_dates[idx], datetime.min.time()) < start:
            idx += 1
        if idx >= len(sorted_dates):
            return None
        current_date = None
        while idx < len(sorted_dates) and stage_idx < len(stage_requirements):
            date_key = sorted_dates[idx]
            weather = weather_by_date.get(date_key)
            if weather is None:
                idx += 1
                continue
            # Use current stage's temperature profile for daily GDD
            temp_profile = stage_requirements[stage_idx].temperature
            daily_gdd = temp_profile.daily_gdd(weather.temperature_2m_mean)
            remaining[stage_idx] -= daily_gdd
            current_date = datetime.combine(date_key, datetime.min.time())
            # Move to next stage if current met
            while stage_idx < len(stage_requirements) and remaining[stage_idx] <= 0.0:
                # Carry over surplus GDD to next stage if any
                surplus = -remaining[stage_idx]
                stage_idx += 1
                if stage_idx < len(stage_requirements):
                    remaining[stage_idx] -= surplus
            if stage_idx >= len(stage_requirements):
                completion_date = current_date
                break
            idx += 1
        if completion_date is None:
            return None
        growth_days = (completion_date - start).days + 1
        yield_factor = self._calculate_yield_factor_for_period(
            start,
            completion_date,
            weather_by_date,
            stage_requirements,
        )
        return completion_date, growth_days, yield_factor

    def _calculate_yield_factor_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        weather_by_date: dict,
        stage_requirements: List
    ) -> float:
        """Calculate yield_factor for a cultivation period.
        
        Args:
            start_date: Cultivation start date
            end_date: Cultivation end date
            weather_by_date: Dict mapping date to WeatherData
            stage_requirements: List of StageRequirement entities
            
        Returns:
            Yield factor (0-1): 1.0 = no impact, 0.0 = complete loss
        """
        accumulator = YieldImpactAccumulator()
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        # Accumulate temperature stress impacts for each day
        while current_date <= end_date_only:
            if current_date in weather_by_date:
                weather = weather_by_date[current_date]
                
                # Find the appropriate temperature profile for this date
                # For now, use a simple approach: use the first stage's temperature profile
                # TODO: In the future, track stage progression and use stage-specific profiles
                temperature_profile = stage_requirements[0].temperature
                
                # Calculate daily stress impacts
                daily_impacts = temperature_profile.calculate_daily_stress_impacts(weather)
                accumulator.accumulate_daily_impact(daily_impacts)
            
            # Move to next day
            current_date = current_date + timedelta(days=1)
        
        return accumulator.get_yield_factor()
    
    def _evaluate_candidates(
        self, request: OptimalGrowthPeriodRequestDTO, candidate_start_dates: List[datetime]
    ) -> List[CandidateResultDTO]:
        """Evaluate all candidate start dates.
        
        Args:
            request: Request DTO with evaluation parameters
            candidate_start_dates: List of candidate start dates to evaluate
            
        Returns:
            List of evaluation results for each candidate
        """
        candidates = []
        
        for start_date in candidate_start_dates:
            candidate_result = self._evaluate_single_candidate(
                start_date=start_date,
                crop_id=request.crop_id,
                variety=request.variety,
                weather_data_file=request.weather_data_file,
                field=request.field,
                completion_deadline=request.evaluation_period_end,
            )
            candidates.append(candidate_result)
        
        return candidates

    def _evaluate_single_candidate(
        self,
        start_date: datetime,
        crop_id: str,
        variety: Optional[str],
        weather_data: List[WeatherData],
        field: Field,
        crop: Crop,
        completion_deadline: datetime,
    ) -> CandidateResultDTO:
        """Evaluate a single candidate start date.
        
        Args:
            start_date: Candidate cultivation start date
            crop_id: Crop identifier
            variety: Optional variety
            weather_data: List of weather data entities
            field: Field entity for cost calculation
            completion_deadline: Deadline for completion (cultivation must finish by this date)
            
        Returns:
            CandidateResultDTO with evaluation results. If completion date exceeds deadline,
            total_cost will be None indicating invalid candidate.
        """
        # Create request for growth progress calculation
        progress_request = GrowthProgressCalculateRequestDTO(
            crop_id=crop_id,
            variety=variety,
            start_date=start_date,
            weather_data=weather_data,
        )
        
        # Calculate growth progress
        progress_response = self.growth_progress_interactor.execute(progress_request)
        
        # Find completion date (first date with 100% growth)
        completion_date = None
        growth_days = None
        
        for record in progress_response.progress_records:
            if record.is_complete:
                completion_date = record.date
                # Check if completion date meets the deadline
                if completion_date <= completion_deadline:
                    growth_days = (completion_date - start_date).days + 1  # Include start day
                # If exceeds deadline, leave growth_days as None (invalid candidate)
                break
        
        # Get yield factor from progress response (defaults to 1.0 if not available)
        yield_factor = progress_response.yield_factor if progress_response.yield_factor is not None else 1.0
        
        # Create candidate with field and crop entities (calculation happens in get_metrics())
        return CandidateResultDTO(
            start_date=start_date,
            completion_date=completion_date,
            growth_days=growth_days,
            field=field if growth_days is not None else None,
            crop=crop if growth_days is not None else None,
            is_optimal=False,  # Will be updated later
            yield_factor=yield_factor,
        )

    def _filter_shortest_candidates_per_completion_date(
        self, candidates: List[CandidateResultDTO]
    ) -> List[CandidateResultDTO]:
        """Filter candidates to keep only the shortest cultivation period per completion date.
        
        When multiple candidates reach the same completion date, we only keep the one with
        the shortest growth_days (i.e., the one that starts latest). This is optimal because:
        - Same completion date means same deadline constraint satisfaction
        - Shorter period means lower total cost (growth_days × daily_fixed_cost)
        - Later start may have better yield_factor due to better weather conditions
        
        Args:
            candidates: List of candidate results to filter
            
        Returns:
            Filtered list with only the shortest candidate per completion date,
            ordered by completion_date descending (future to past)
        """
        # Group candidates by completion_date
        completion_groups: Dict[datetime, List[CandidateResultDTO]] = defaultdict(list)
        
        for candidate in candidates:
            if candidate.completion_date is not None and candidate.growth_days is not None:
                completion_groups[candidate.completion_date].append(candidate)
        
        # Select shortest candidate from each group
        filtered = []
        for completion_date in sorted(completion_groups.keys(), reverse=True):  # Future to past
            group = completion_groups[completion_date]
            # Find candidate with minimum growth_days
            shortest = min(group, key=lambda c: c.growth_days)
            filtered.append(shortest)
        
        return filtered

    def _get_crop_profile(
        self, crop_id: str, variety: Optional[str]
    ) -> CropProfile:
        """Get crop profile from gateway."""
        return self.crop_profile_gateway.get()

