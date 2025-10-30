"""In-memory gateway for fertilizer recommendation (for testing/CLI integration)."""

from typing import Any, Dict, List

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.fertilizer_recommendation_entity import (
    FertilizerPlan,
    FertilizerApplication,
    Nutrients,
)
from agrr_core.usecase.gateways.fertilizer_recommend_gateway import FertilizerRecommendGateway

class FertilizerRecommendInMemoryGateway(FertilizerRecommendGateway):
    def recommend(self, crop_profile: Dict[str, Any]) -> FertilizerPlan:
        crop_info = crop_profile.get("crop", {})
        crop = Crop(
            crop_id=crop_info.get("crop_id", "unknown"),
            name=crop_info.get("name", "Unknown"),
            area_per_unit=crop_info.get("area_per_unit", 1.0),
            variety=crop_info.get("variety"),
            revenue_per_area=crop_info.get("revenue_per_area"),
            max_revenue=crop_info.get("max_revenue"),
            groups=crop_info.get("groups"),
        )

        # Simple defaults for demonstration/testing (not agronomic truth)
        # Totals scale mildly with area_per_unit just as a placeholder logic
        totals = Nutrients(N=18.0, P=5.0, K=12.0)
        applications: List[FertilizerApplication] = [
            FertilizerApplication(
                application_type="basal",
                count=1,
                schedule_hint="pre-plant",
                nutrients=Nutrients(N=6.0, P=2.0, K=3.0),
            ),
            FertilizerApplication(
                application_type="topdress",
                count=2,
                schedule_hint="fruiting",
                nutrients=Nutrients(N=12.0, P=3.0, K=9.0),
                per_application=Nutrients(N=6.0, P=1.5, K=4.5),
            ),
        ]

        return FertilizerPlan(
            crop=crop,
            totals=totals,
            applications=applications,
            sources=["inmemory"],
            confidence=0.5,
            notes="In-memory gateway placeholder",
        )

