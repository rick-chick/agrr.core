import asyncio
import pytest

from agrr_core.usecase.interactors.fertilizer_llm_recommend_interactor import (
    FertilizerLLMRecommendInteractor,
    FertilizerRecommendRequestDTO,
)
from tests.conftest import fake_gateway_valid, fake_gateway_bad_totals, crop_profile_sample


@pytest.mark.asyncio
async def test_recommend_happy_path(fake_gateway_valid, crop_profile_sample):
    gateway = fake_gateway_valid
    interactor = FertilizerLLMRecommendInteractor(gateway)
    req = FertilizerRecommendRequestDTO(crop_profile=crop_profile_sample)
    plan = await interactor.execute(req)

    assert plan.totals.N == pytest.approx(18.0)
    assert plan.totals.P == pytest.approx(5.2)
    assert plan.totals.K == pytest.approx(12.4)
    assert len(plan.applications) >= 1
    # Sums
    sumN = sum(a.nutrients.N for a in plan.applications)
    sumP = sum(a.nutrients.P for a in plan.applications)
    sumK = sum(a.nutrients.K for a in plan.applications)
    assert sumN == pytest.approx(plan.totals.N)
    assert sumP == pytest.approx(plan.totals.P)
    assert sumK == pytest.approx(plan.totals.K)


@pytest.mark.asyncio
async def test_recommend_validation_sum_mismatch(fake_gateway_bad_totals, crop_profile_sample):
    gateway = fake_gateway_bad_totals
    interactor = FertilizerLLMRecommendInteractor(gateway)
    req = FertilizerRecommendRequestDTO(crop_profile=crop_profile_sample)
    with pytest.raises(ValueError):
        await interactor.execute(req)


