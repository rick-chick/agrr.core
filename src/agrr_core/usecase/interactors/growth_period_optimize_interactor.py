"""Optimal growth period calculation interactor.

This interactor finds the optimal cultivation start date that minimizes total cost
based on daily fixed costs, while ensuring completion by a specified deadline.

The optimization follows this logic:
1. Generate candidate start dates from earliest_start_date to completion_deadline
2. For each candidate, calculate cultivation progress until 100% completion
3. Filter out candidates that cannot complete by the deadline
4. Calculate total cost = growth_days * daily_fixed_cost for valid candidates
5. Select the candidate with minimum total cost

The evaluation period has dual meaning:
- evaluation_period_start: Earliest possible cultivation start date
- evaluation_period_end: Completion deadline (cultivation must finish by this date)
"""

from datetime import datetime, timedelta
from typing import List, Optional

from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import (
    CropRequirementCraftRequestDTO,
)
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
from agrr_core.usecase.gateways.crop_requirement_gateway import CropRequirementGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.optimization_result_gateway import (
    OptimizationResultGateway,
)
from agrr_core.usecase.interactors.growth_progress_calculate_interactor import (
    GrowthProgressCalculateInteractor,
)
from agrr_core.usecase.ports.input.growth_period_optimize_input_port import (
    GrowthPeriodOptimizeInputPort,
)
from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)


class GrowthPeriodOptimizeInteractor(GrowthPeriodOptimizeInputPort):
    """Interactor for finding optimal growth period with minimum cost."""

    def __init__(
        self,
        crop_requirement_gateway: CropRequirementGateway,
        weather_gateway: WeatherGateway,
        optimization_result_gateway: OptimizationResultGateway = None,
    ):
        self.crop_requirement_gateway = crop_requirement_gateway
        self.weather_gateway = weather_gateway
        self.optimization_result_gateway = optimization_result_gateway
        
        # Use existing growth progress calculator
        self.growth_progress_interactor = GrowthProgressCalculateInteractor(
            crop_requirement_gateway=crop_requirement_gateway,
            weather_gateway=weather_gateway,
        )

    async def execute(
        self, request: OptimalGrowthPeriodRequestDTO
    ) -> OptimalGrowthPeriodResponseDTO:
        """Calculate optimal growth period using efficient sliding window algorithm.

        Args:
            request: Request DTO containing crop info, evaluation period, and cost parameters

        Returns:
            Response DTO containing optimal period and all candidate evaluations
            
        Raises:
            ValueError: If no candidate reaches 100% growth completion
        """
        # Use efficient sliding window algorithm
        candidates = await self._evaluate_candidates_efficient(request)
        
        # Find optimal candidate (minimum cost, excluding failures and deadline violations)
        valid_candidates = [c for c in candidates if c.total_cost is not None]
        
        if not valid_candidates:
            # Check if any candidate completed but exceeded deadline
            completed_candidates = [c for c in candidates if c.completion_date is not None]
            if completed_candidates:
                earliest_completion = min(c.completion_date for c in completed_candidates)
                raise ValueError(
                    f"No candidate can complete by the deadline ({request.evaluation_period_end.date()}). "
                    f"Earliest possible completion is {earliest_completion.date()}. "
                    f"Consider extending the deadline or choosing an earlier start date range."
                )
            else:
                raise ValueError(
                    "No candidate reached 100% growth completion. "
                    "Consider extending weather data or choosing different start dates."
                )
        
        optimal_candidate = min(valid_candidates, key=lambda c: c.total_cost)
        
        # Mark optimal candidate
        for candidate in candidates:
            if candidate.start_date == optimal_candidate.start_date:
                # Create new candidate with is_optimal=True
                object.__setattr__(candidate, 'is_optimal', True)
        
        # Get crop info for response
        crop_requirement = await self._get_crop_requirements(
            request.crop_id, request.variety
        )
        
        return OptimalGrowthPeriodResponseDTO(
            crop_name=crop_requirement.crop.name,
            variety=crop_requirement.crop.variety,
            optimal_start_date=optimal_candidate.start_date,
            completion_date=optimal_candidate.completion_date,
            growth_days=optimal_candidate.growth_days,
            total_cost=optimal_candidate.total_cost,
            daily_fixed_cost=request.daily_fixed_cost,
            candidates=candidates,
        )

    async def _evaluate_candidates_efficient(
        self, request: OptimalGrowthPeriodRequestDTO
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
        # Get crop requirements and weather data
        if request.crop_requirement_file:
            # Load from file (fast, no LLM)
            crop_requirement = await self.crop_requirement_gateway.get(
                request.crop_requirement_file
            )
        else:
            # Use LLM to generate (slow)
            crop_requirement = await self._get_crop_requirements(
                request.crop_id, request.variety
            )
        weather_data = await self.weather_gateway.get(request.weather_data_file)
        
        # Calculate total required GDD
        total_required_gdd = sum(
            stage_req.thermal.required_gdd 
            for stage_req in crop_requirement.stage_requirements
        )
        
        # Get base temperature from first stage (assuming same for all stages)
        base_temp = crop_requirement.stage_requirements[0].temperature.base_temperature
        
        # Create weather data lookup by date
        weather_by_date = {w.time.date(): w for w in weather_data}
        
        # Sort dates to ensure chronological order
        sorted_dates = sorted(weather_by_date.keys())
        
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
        
        # Find first completion
        while window_end_idx < len(sorted_dates) and accumulated_gdd < total_required_gdd:
            date = sorted_dates[window_end_idx]
            if date >= current_start.date():
                weather = weather_by_date[date]
                daily_gdd = max(0, weather.temperature_2m_mean - base_temp)
                accumulated_gdd += daily_gdd
                window_end_idx += 1
            else:
                window_end_idx += 1
                continue
        
        # Check if first candidate completes
        if accumulated_gdd >= total_required_gdd and window_end_idx > 0:
            completion_date = datetime.combine(sorted_dates[window_end_idx - 1], datetime.min.time())
            if completion_date <= request.evaluation_period_end:
                growth_days = (completion_date - current_start).days + 1
                total_cost = growth_days * request.daily_fixed_cost
                results.append(CandidateResultDTO(
                    start_date=current_start,
                    completion_date=completion_date,
                    growth_days=growth_days,
                    total_cost=total_cost,
                    is_optimal=False
                ))
                gdd_per_candidate.append(accumulated_gdd)
            else:
                # Exceeds deadline
                results.append(CandidateResultDTO(
                    start_date=current_start,
                    completion_date=completion_date,
                    growth_days=None,
                    total_cost=None,
                    is_optimal=False
                ))
                gdd_per_candidate.append(accumulated_gdd)
        
        # Slide window: move start date forward one day at a time
        while current_start < request.evaluation_period_end:
            # Move start date forward
            prev_start = current_start
            current_start += timedelta(days=1)
            
            # Remove GDD from the day that's no longer in the window
            if prev_start.date() in weather_by_date:
                weather = weather_by_date[prev_start.date()]
                daily_gdd = max(0, weather.temperature_2m_mean - base_temp)
                accumulated_gdd -= daily_gdd
            
            # Add days at the end until we reach required GDD again
            while accumulated_gdd < total_required_gdd and window_end_idx < len(sorted_dates):
                date = sorted_dates[window_end_idx]
                weather = weather_by_date[date]
                daily_gdd = max(0, weather.temperature_2m_mean - base_temp)
                accumulated_gdd += daily_gdd
                window_end_idx += 1
            
            # Check if this candidate is valid
            if accumulated_gdd >= total_required_gdd and window_end_idx > 0:
                completion_date = datetime.combine(sorted_dates[window_end_idx - 1], datetime.min.time())
                if completion_date <= request.evaluation_period_end:
                    growth_days = (completion_date - current_start).days + 1
                    total_cost = growth_days * request.daily_fixed_cost
                    results.append(CandidateResultDTO(
                        start_date=current_start,
                        completion_date=completion_date,
                        growth_days=growth_days,
                        total_cost=total_cost,
                        is_optimal=False
                    ))
                    gdd_per_candidate.append(accumulated_gdd)
                else:
                    # Completion exceeds deadline - stop here
                    break
            else:
                # Cannot complete within available weather data
                break
        
        # Save intermediate results if gateway is available
        if self.optimization_result_gateway:
            intermediate_results = []
            for idx, candidate in enumerate(results):
                intermediate_result = OptimizationIntermediateResult(
                    start_date=candidate.start_date,
                    completion_date=candidate.completion_date,
                    growth_days=candidate.growth_days,
                    accumulated_gdd=gdd_per_candidate[idx] if idx < len(gdd_per_candidate) else 0.0,
                    total_cost=candidate.total_cost,
                    is_optimal=candidate.is_optimal,
                    base_temperature=base_temp,
                )
                intermediate_results.append(intermediate_result)
            
            # Generate optimization ID from request parameters
            optimization_id = f"{request.crop_id}_{request.variety or 'default'}_{request.evaluation_period_start.date()}_{request.evaluation_period_end.date()}"
            await self.optimization_result_gateway.save(optimization_id, intermediate_results)
        
        return results

    async def _evaluate_candidates(
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
            candidate_result = await self._evaluate_single_candidate(
                start_date=start_date,
                crop_id=request.crop_id,
                variety=request.variety,
                weather_data_file=request.weather_data_file,
                daily_fixed_cost=request.daily_fixed_cost,
                completion_deadline=request.evaluation_period_end,
            )
            candidates.append(candidate_result)
        
        return candidates

    async def _evaluate_single_candidate(
        self,
        start_date: datetime,
        crop_id: str,
        variety: Optional[str],
        weather_data_file: str,
        daily_fixed_cost: float,
        completion_deadline: datetime,
    ) -> CandidateResultDTO:
        """Evaluate a single candidate start date.
        
        Args:
            start_date: Candidate cultivation start date
            crop_id: Crop identifier
            variety: Optional variety
            weather_data_file: Weather data file path
            daily_fixed_cost: Daily fixed cost
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
            weather_data_file=weather_data_file,
        )
        
        # Calculate growth progress
        progress_response = await self.growth_progress_interactor.execute(progress_request)
        
        # Find completion date (first date with 100% growth)
        completion_date = None
        growth_days = None
        total_cost = None
        
        for record in progress_response.progress_records:
            if record.is_complete:
                completion_date = record.date
                # Check if completion date meets the deadline
                if completion_date <= completion_deadline:
                    growth_days = (completion_date - start_date).days + 1  # Include start day
                    total_cost = growth_days * daily_fixed_cost
                # If exceeds deadline, leave total_cost as None (invalid candidate)
                break
        
        return CandidateResultDTO(
            start_date=start_date,
            completion_date=completion_date,
            growth_days=growth_days,
            total_cost=total_cost,
            is_optimal=False,  # Will be updated later
        )

    async def _get_crop_requirements(
        self, crop_id: str, variety: Optional[str]
    ) -> CropRequirementAggregate:
        """Get crop requirements from gateway (uses LLM)."""
        craft_request = CropRequirementCraftRequestDTO(
            crop_query=f"{crop_id} {variety}" if variety else crop_id
        )
        return await self.crop_requirement_gateway.craft(craft_request)

