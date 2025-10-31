import pytest
from datetime import datetime, timedelta

from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.dto.growth_period_optimize_request_dto import OptimalGrowthPeriodRequestDTO
from agrr_core.usecase.dto.growth_progress_calculate_request_dto import GrowthProgressCalculateRequestDTO
from agrr_core.usecase.interactors.growth_period_optimize_interactor import GrowthPeriodOptimizeInteractor
from agrr_core.usecase.interactors.growth_progress_calculate_interactor import GrowthProgressCalculateInteractor


@pytest.mark.unit
def test_allocate_and_progress_end_on_same_date(
    gateway_crop_profile_two_stage,
    gateway_weather_constant,
    entity_weather_constant_20c_200d,
):
    """
    One crop, two stages with different base/max temperatures.
    Start from allocated start date; ensure allocate (optimal growth period) completion
    date equals the date progress reaches is_complete.
    """
    # Common start/end for evaluation
    start_date = entity_weather_constant_20c_200d[0].time
    deadline = start_date + timedelta(days=60)

    # Build interactors with in-memory gateways
    field = Field(field_id="F1", name="Field1", area=1000.0, daily_fixed_cost=10.0)

    growth_period_interactor = GrowthPeriodOptimizeInteractor(
        crop_profile_gateway=gateway_crop_profile_two_stage,
        weather_gateway=gateway_weather_constant,
    )

    request = OptimalGrowthPeriodRequestDTO(
        crop_id="testcrop",
        variety="v1",
        evaluation_period_start=start_date,
        evaluation_period_end=deadline,
        field=field,
        filter_redundant_candidates=True,
        early_stop_at_first=True,
    )

    period_response = growth_period_interactor.execute(request)

    # Pick the candidate that starts on our start_date
    candidates = [c for c in period_response.candidates if c.start_date == start_date and c.completion_date is not None]
    assert candidates, "No valid candidate for the specified start date"
    allocate_completion = candidates[0].completion_date

    # Calculate progress timeline from the same start
    progress_interactor = GrowthProgressCalculateInteractor(
        crop_profile_gateway=gateway_crop_profile_two_stage,
        weather_gateway=gateway_weather_constant,
    )

    progress_request = GrowthProgressCalculateRequestDTO(
        crop_id="testcrop",
        variety="v1",
        start_date=start_date,
    )

    progress_response = progress_interactor.execute(progress_request)
    # Find first day where is_complete is True
    complete_days = [r for r in progress_response.progress_records if r.is_complete]
    assert complete_days, "Progress never reached completion"
    progress_completion = complete_days[0].date

    # Compare dates
    assert allocate_completion == progress_completion


@pytest.mark.unit
def test_allocate_and_progress_end_on_same_date_single_stage(
    gateway_crop_profile_single_stage,
    gateway_weather_constant,
    entity_weather_constant_20c_200d,
):
    """
    Single-stage crop: ensure allocate completion date equals progress completion
    date when starting from the same start date.
    """
    start_date = entity_weather_constant_20c_200d[0].time
    deadline = start_date + timedelta(days=60)

    field = Field(field_id="F1", name="Field1", area=1000.0, daily_fixed_cost=10.0)

    growth_period_interactor = GrowthPeriodOptimizeInteractor(
        crop_profile_gateway=gateway_crop_profile_single_stage,
        weather_gateway=gateway_weather_constant,
    )

    request = OptimalGrowthPeriodRequestDTO(
        crop_id="singlecrop",
        variety="v1",
        evaluation_period_start=start_date,
        evaluation_period_end=deadline,
        field=field,
        filter_redundant_candidates=True,
        early_stop_at_first=True,
    )

    period_response = growth_period_interactor.execute(request)
    candidates = [c for c in period_response.candidates if c.start_date == start_date and c.completion_date is not None]
    assert candidates, "No valid candidate for the specified start date"
    allocate_completion = candidates[0].completion_date

    progress_interactor = GrowthProgressCalculateInteractor(
        crop_profile_gateway=gateway_crop_profile_single_stage,
        weather_gateway=gateway_weather_constant,
    )

    progress_request = GrowthProgressCalculateRequestDTO(
        crop_id="singlecrop",
        variety="v1",
        start_date=start_date,
    )

    progress_response = progress_interactor.execute(progress_request)
    complete_days = [r for r in progress_response.progress_records if r.is_complete]
    assert complete_days, "Progress never reached completion"
    progress_completion = complete_days[0].date

    assert allocate_completion == progress_completion


@pytest.mark.unit
def test_allocate_and_progress_end_on_same_date_three_stage(
    gateway_crop_profile_three_stage,
    gateway_weather_constant,
    entity_weather_constant_20c_200d,
):
    """
    Three-stage crop: ensure allocate completion date equals progress completion
    date when starting from the same start date under constant weather.
    """
    start_date = entity_weather_constant_20c_200d[0].time
    deadline = start_date + timedelta(days=90)

    field = Field(field_id="F1", name="Field1", area=1000.0, daily_fixed_cost=10.0)

    growth_period_interactor = GrowthPeriodOptimizeInteractor(
        crop_profile_gateway=gateway_crop_profile_three_stage,
        weather_gateway=gateway_weather_constant,
    )

    request = OptimalGrowthPeriodRequestDTO(
        crop_id="threecrop",
        variety="v1",
        evaluation_period_start=start_date,
        evaluation_period_end=deadline,
        field=field,
        filter_redundant_candidates=True,
        early_stop_at_first=True,
    )

    period_response = growth_period_interactor.execute(request)
    candidates = [c for c in period_response.candidates if c.start_date == start_date and c.completion_date is not None]
    assert candidates, "No valid candidate for the specified start date"
    allocate_completion = candidates[0].completion_date

    progress_interactor = GrowthProgressCalculateInteractor(
        crop_profile_gateway=gateway_crop_profile_three_stage,
        weather_gateway=gateway_weather_constant,
    )

    progress_request = GrowthProgressCalculateRequestDTO(
        crop_id="threecrop",
        variety="v1",
        start_date=start_date,
    )

    progress_response = progress_interactor.execute(progress_request)
    complete_days = [r for r in progress_response.progress_records if r.is_complete]
    assert complete_days, "Progress never reached completion"
    progress_completion = complete_days[0].date

    assert allocate_completion == progress_completion


