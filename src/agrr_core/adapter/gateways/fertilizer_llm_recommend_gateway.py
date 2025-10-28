from typing import Any, Dict, List

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.fertilizer_recommendation_entity import (
	FertilizerPlan,
	FertilizerApplication,
	Nutrients,
)
from agrr_core.usecase.gateways.fertilizer_recommend_gateway import FertilizerRecommendGateway
from agrr_core.framework.services.clients.llm_client import LLMClient


class FertilizerLLMRecommendGateway(FertilizerRecommendGateway):
	def __init__(self, llm_client: LLMClient) -> None:
		self._llm = llm_client

	async def recommend(self, crop_profile: Dict[str, Any]) -> FertilizerPlan:
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

		structure = {
			"crop": {"crop_id": "", "name": ""},
			"totals": {"N": 0.0, "P": 0.0, "K": 0.0},
			"applications": [
				{
					"type": "",
					"count": 1,
					"schedule_hint": "",
					"nutrients": {"N": 0.0, "P": 0.0, "K": 0.0},
					"per_application": {"N": 0.0, "P": 0.0, "K": 0.0},
				}
			],
			"sources": [""],
			"confidence": 0.0,
			"notes": "",
		}

		instruction = (
			"Return JSON only. Units are elemental N,P,K in g/m2. "
			"Ensure totals equal the sum of application nutrients (±1e-6). "
			"Provide 2-5 sources as strings."
		)

		query = f"Crop: {crop.name} ({crop.crop_id}). Provide N/P/K totals and basal/topdress plan."
		resp = await self._llm.struct(query=query, structure=structure, instruction=instruction)
		
		# Handle response format
		if isinstance(resp, str):
			import json
			data = json.loads(resp)
		elif isinstance(resp, dict):
			data = resp.get("data", {})
		else:
			raise ValueError(f"Unexpected response type: {type(resp)}")

		# Handle LLM response variations - normalize to our expected format
		if "nutrient_totals" in data:
			# LLM returned different field names, normalize
			totals_in = data.get("nutrient_totals", {})
			basal_app = data.get("basal_application", {})
			topdress_app = data.get("topdress_application", {})
			
			# Convert to our expected format
			normalized_data = {
				"crop": {"crop_id": crop.crop_id, "name": data.get("crop", crop.name)},
				"totals": totals_in,
				"applications": []
			}
			
			if basal_app:
				normalized_data["applications"].append({
					"type": "basal",
					"count": 1,
					"schedule_hint": "pre-plant",
					"nutrients": basal_app,
					"per_application": None
				})
			
			if topdress_app:
				normalized_data["applications"].append({
					"type": "topdress", 
					"count": 1,
					"schedule_hint": "fruiting",
					"nutrients": topdress_app,
					"per_application": None
				})
			
			normalized_data["sources"] = data.get("sources", [])
			normalized_data["confidence"] = 0.7
			normalized_data["notes"] = "LLM-generated recommendation"
			
			data = normalized_data

		# Fallback to parsed crop if model didn't echo
		crop_out = data.get("crop") or {"crop_id": crop.crop_id, "name": crop.name}
		totals_in = data.get("totals", {})

		applications_in: List[Dict[str, Any]] = data.get("applications", [])
		applications: List[FertilizerApplication] = []
		for app in applications_in:
			per_app_in = app.get("per_application")
			applications.append(
				FertilizerApplication(
					application_type=app.get("type", "basal"),
					count=int(app.get("count", 1)),
					schedule_hint=app.get("schedule_hint") or None,
					nutrients=Nutrients(
						N=float(app.get("nutrients", {}).get("N", 0.0)),
						P=float(app.get("nutrients", {}).get("P", 0.0)),
						K=float(app.get("nutrients", {}).get("K", 0.0)),
					),
					per_application=(
						Nutrients(
							N=float(per_app_in.get("N", 0.0)),
							P=float(per_app_in.get("P", 0.0)),
							K=float(per_app_in.get("K", 0.0)),
						)
						if isinstance(per_app_in, dict)
						else None
					),
				)
			)

		plan = FertilizerPlan(
			crop=Crop(crop_id=crop_out.get("crop_id", crop.crop_id), name=crop_out.get("name", crop.name), area_per_unit=crop.area_per_unit),
			totals=Nutrients(N=float(totals_in.get("N", 0.0)), P=float(totals_in.get("P", 0.0)), K=float(totals_in.get("K", 0.0))),
			applications=applications,
			sources=[s for s in data.get("sources", []) if isinstance(s, str)],
			confidence=float(data.get("confidence", 0.0)),
			notes=data.get("notes") or None,
		)

		return plan
