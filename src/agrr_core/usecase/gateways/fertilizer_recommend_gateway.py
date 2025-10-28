"""Gateway interface for LLM-based fertilizer recommendation."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from agrr_core.entity.entities.fertilizer_recommendation_entity import FertilizerPlan


class FertilizerRecommendGateway(ABC):
    """Boundary for obtaining structured fertilizer recommendations via LLM/retrieval.

    Implementations may call external LLMs or deterministic stubs. The UseCase
    layer depends only on this interface.
    """

    @abstractmethod
    async def recommend(self, crop_profile: Dict[str, Any]) -> FertilizerPlan:
        """Return a fertilizer plan for the given crop profile.

        Args:
            crop_profile: Parsed object produced by `agrr crop` CLI.

        Returns:
            FertilizerPlan: Structured recommendation in g/m2.
        """
        raise NotImplementedError


