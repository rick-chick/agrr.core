"""Optimal growth period calculation interactor.

This interactor finds the optimal growth start date that minimizes total cost
based on daily fixed costs. It evaluates multiple candidate start dates and
selects the one with the shortest growth period (lowest total cost).

The optimization follows this logic:
1. For each candidate start date, calculate growth progress until 100%
2. Calculate total cost = growth_days * daily_fixed_cost
3. Select the candidate with minimum total cost
"""

from datetime import datetime
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
from agrr_core.usecase.interactors.growth_progress_calculate_interactor import (
    GrowthProgressCalculateInteractor,
)
from agrr_core.usecase.ports.input.growth_period_optimize_input_port import (
    GrowthPeriodOptimizeInputPort,
)


class GrowthPeriodOptimizeInteractor(GrowthPeriodOptimizeInputPort):
    """Interactor for finding optimal growth period with minimum cost."""

    def __init__(
        self,
        crop_requirement_gateway: CropRequirementGateway,
        weather_gateway: WeatherGateway,
    ):
        self.crop_requirement_gateway = crop_requirement_gateway
        self.weather_gateway = weather_gateway
        
        # Use existing growth progress calculator
        self.growth_progress_interactor = GrowthProgressCalculateInteractor(
            crop_requirement_gateway=crop_requirement_gateway,
            weather_gateway=weather_gateway,
        )

    async def execute(
        self, request: OptimalGrowthPeriodRequestDTO
    ) -> OptimalGrowthPeriodResponseDTO:
        """Calculate optimal growth period.

        Args:
            request: Request DTO containing crop info, candidate dates, and cost parameters

        Returns:
            Response DTO containing optimal period and all candidate evaluations
            
        Raises:
            ValueError: If no candidate reaches 100% growth completion
        """
        # Evaluate all candidates
        candidates = await self._evaluate_candidates(request)
        
        # Find optimal candidate (minimum cost, excluding failures)
        valid_candidates = [c for c in candidates if c.total_cost is not None]
        
        if not valid_candidates:
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

    async def _evaluate_candidates(
        self, request: OptimalGrowthPeriodRequestDTO
    ) -> List[CandidateResultDTO]:
        """Evaluate all candidate start dates."""
        candidates = []
        
        for start_date in request.candidate_start_dates:
            candidate_result = await self._evaluate_single_candidate(
                start_date=start_date,
                crop_id=request.crop_id,
                variety=request.variety,
                weather_data_file=request.weather_data_file,
                daily_fixed_cost=request.daily_fixed_cost,
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
    ) -> CandidateResultDTO:
        """Evaluate a single candidate start date."""
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
                growth_days = (completion_date - start_date).days + 1  # Include start day
                total_cost = growth_days * daily_fixed_cost
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
        """Get crop requirements from gateway."""
        craft_request = CropRequirementCraftRequestDTO(
            crop_query=f"{crop_id} {variety}" if variety else crop_id
        )
        return await self.crop_requirement_gateway.craft(craft_request)

