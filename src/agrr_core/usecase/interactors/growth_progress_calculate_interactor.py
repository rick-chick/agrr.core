"""Growth progress calculation interactor.

This interactor calculates daily growth progress based on GDD (Growing Degree Days)
accumulation from a given start date using crop requirements and weather data.

The calculation follows a simple linear GDD accumulation model:
- Total required GDD = sum of all stage requirements
- Daily progress = (cumulative GDD / total required GDD) * 100
"""

from datetime import timedelta
from typing import List

from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)
from agrr_core.entity.entities.growth_progress_entity import GrowthProgress
from agrr_core.entity.entities.growth_progress_timeline_entity import (
    GrowthProgressTimeline,
)
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import (
    CropRequirementCraftRequestDTO,
)
from agrr_core.usecase.dto.growth_progress_calculate_request_dto import (
    GrowthProgressCalculateRequestDTO,
)
from agrr_core.usecase.dto.growth_progress_calculate_response_dto import (
    GrowthProgressCalculateResponseDTO,
    GrowthProgressRecordDTO,
)
from agrr_core.usecase.gateways.crop_requirement_gateway import CropRequirementGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.ports.input.growth_progress_calculate_input_port import (
    GrowthProgressCalculateInputPort,
)


class GrowthProgressCalculateInteractor(GrowthProgressCalculateInputPort):
    """Interactor for calculating growth progress timeline."""

    def __init__(
        self,
        crop_requirement_gateway: CropRequirementGateway,
        weather_gateway: WeatherGateway,
    ):
        self.crop_requirement_gateway = crop_requirement_gateway
        self.weather_gateway = weather_gateway

    async def execute(
        self, request: GrowthProgressCalculateRequestDTO
    ) -> GrowthProgressCalculateResponseDTO:
        """Calculate growth progress timeline.

        Args:
            request: Request DTO containing crop info, location, and date range

        Returns:
            Response DTO containing daily growth progress records
        """
        # Step 1: Get crop requirements
        crop_requirement = await self._get_crop_requirements(
            request.crop_id, request.variety
        )

        # Step 2: Get weather data from file
        weather_data_list = await self._get_weather_data(request.weather_data_file)

        # Step 3: Calculate growth progress timeline
        timeline = self._calculate_growth_progress(
            crop_requirement, request.start_date, weather_data_list
        )

        # Step 4: Convert to response DTO
        return self._to_response_dto(timeline)

    async def _get_crop_requirements(
        self, crop_id: str, variety: str
    ) -> CropRequirementAggregate:
        """Get crop requirements from gateway."""
        craft_request = CropRequirementCraftRequestDTO(
            crop_query=f"{crop_id} {variety}" if variety else crop_id
        )
        return await self.crop_requirement_gateway.craft(craft_request)

    async def _get_weather_data(self, source: str) -> List[WeatherData]:
        """Get weather data from gateway.

        Args:
            source: Data source identifier

        Returns:
            List of WeatherData entities
        """
        return await self.weather_gateway.get(source)

    def _calculate_growth_progress(
        self,
        crop_requirement: CropRequirementAggregate,
        start_date,
        weather_data_list: List[WeatherData],
    ) -> GrowthProgressTimeline:
        """Calculate growth progress based on GDD accumulation."""
        # Calculate total required GDD
        total_required_gdd = sum(
            sr.thermal.required_gdd for sr in crop_requirement.stage_requirements
        )

        if total_required_gdd <= 0:
            raise ValueError("Total required GDD must be positive")

        cumulative_gdd = 0.0
        progress_list = []

        for weather_data in weather_data_list:
            # Determine current stage based on cumulative GDD
            current_stage = self._determine_current_stage(
                cumulative_gdd, crop_requirement.stage_requirements
            )

            # Calculate daily GDD using the current stage's temperature profile
            daily_gdd = current_stage.daily_gdd(weather_data)
            cumulative_gdd += daily_gdd

            # Calculate growth percentage (cap at 100%)
            growth_percentage = min(
                (cumulative_gdd / total_required_gdd) * 100.0, 100.0
            )

            # Create progress record
            progress = GrowthProgress(
                date=weather_data.time,
                cumulative_gdd=cumulative_gdd,
                total_required_gdd=total_required_gdd,
                growth_percentage=growth_percentage,
                current_stage=current_stage.stage,
                is_complete=(growth_percentage >= 100.0),
            )
            progress_list.append(progress)

        return GrowthProgressTimeline(
            crop=crop_requirement.crop,
            start_date=start_date,
            progress_list=progress_list,
        )

    def _determine_current_stage(
        self, cumulative_gdd: float, stage_requirements: List[StageRequirement]
    ) -> StageRequirement:
        """Determine the current growth stage based on cumulative GDD.

        The stage is determined by checking which stage the cumulative GDD falls into.
        Stages are ordered, and we accumulate GDD requirements until we exceed cumulative_gdd.
        """
        accumulated = 0.0
        for sr in stage_requirements:
            accumulated += sr.thermal.required_gdd
            if cumulative_gdd < accumulated:
                return sr

        # If we've exceeded all stages, return the last stage
        return stage_requirements[-1]

    def _to_response_dto(
        self, timeline: GrowthProgressTimeline
    ) -> GrowthProgressCalculateResponseDTO:
        """Convert timeline entity to response DTO."""
        progress_records = [
            GrowthProgressRecordDTO(
                date=progress.date,
                cumulative_gdd=progress.cumulative_gdd,
                total_required_gdd=progress.total_required_gdd,
                growth_percentage=progress.growth_percentage,
                stage_name=progress.current_stage.name,
                is_complete=progress.is_complete,
            )
            for progress in timeline.progress_list
        ]

        return GrowthProgressCalculateResponseDTO(
            crop_name=timeline.crop.name,
            variety=timeline.crop.variety,
            start_date=timeline.start_date,
            progress_records=progress_records,
        )

