"""Interactor: fertilizer LLM recommend."""

from dataclasses import dataclass
from typing import Any, Dict

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.fertilizer_recommendation_entity import (
    FertilizerPlan,
    FertilizerApplication,
    Nutrients,
)
from agrr_core.usecase.gateways.fertilizer_recommend_gateway import FertilizerRecommendGateway


@dataclass
class FertilizerRecommendRequestDTO:
    crop_profile: Dict[str, Any]


class FertilizerLLMRecommendInteractor:
    """UseCase interactor for fertilizer recommendation via LLM gateway."""

    def __init__(self, gateway: FertilizerRecommendGateway) -> None:
        self._gateway = gateway

    async def execute(self, request: FertilizerRecommendRequestDTO) -> FertilizerPlan:
        plan = await self._gateway.recommend(request.crop_profile)
        self._validate_plan(plan)
        return plan

    def _validate_plan(self, plan: FertilizerPlan) -> None:
        # Basic non-negative totals
        if plan.totals.N < 0 or plan.totals.P < 0 or plan.totals.K < 0:
            raise ValueError("Totals must be non-negative")

        if not plan.applications:
            raise ValueError("At least one application is required")

        # Sum applications and compare to totals
        sum_N = sum(app.nutrients.N for app in plan.applications)
        sum_P = sum(app.nutrients.P for app in plan.applications)
        sum_K = sum(app.nutrients.K for app in plan.applications)

        eps = 1e-6
        if abs(sum_N - plan.totals.N) > eps or abs(sum_P - plan.totals.P) > eps or abs(sum_K - plan.totals.K) > eps:
            raise ValueError("Application sums must equal totals for N, P, K")

        # Validate each application
        for app in plan.applications:
            if app.count < 1:
                raise ValueError("Application count must be >= 1")
            if app.per_application and app.count > 1:
                # per_application * count should match group totals
                if (
                    abs(app.per_application.N * app.count - app.nutrients.N) > eps
                    or abs(app.per_application.P * app.count - app.nutrients.P) > eps
                    or abs(app.per_application.K * app.count - app.nutrients.K) > eps
                ):
                    raise ValueError("per_application * count must match group nutrients")


