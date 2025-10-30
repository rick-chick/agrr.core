"""Presenter for fertilizer recommendation CLI output."""

import json
from typing import Any, Dict

from agrr_core.entity.entities.fertilizer_recommendation_entity import FertilizerPlan

class FertilizerRecommendCliPresenter:
    @staticmethod
    def to_dict(plan: FertilizerPlan) -> Dict[str, Any]:
        return {
            "crop": {"crop_id": plan.crop.crop_id, "name": plan.crop.name},
            "totals": {"N": plan.totals.N, "P": plan.totals.P, "K": plan.totals.K},
            "applications": [
                {
                    "type": app.application_type,
                    "count": app.count,
                    "schedule_hint": app.schedule_hint,
                    "nutrients": {"N": app.nutrients.N, "P": app.nutrients.P, "K": app.nutrients.K},
                    "per_application": (
                        {"N": app.per_application.N, "P": app.per_application.P, "K": app.per_application.K}
                        if app.per_application else None
                    ),
                }
                for app in plan.applications
            ],
            "sources": list(plan.sources),
            "confidence": plan.confidence,
            "notes": plan.notes,
        }

    @classmethod
    def to_json(cls, plan: FertilizerPlan) -> str:
        return json.dumps(cls.to_dict(plan), ensure_ascii=False)

