import argparse
import json
import pytest

from agrr_core.adapter.controllers.fertilizer_cli_recommend_controller import FertilizerCliRecommendController
from agrr_core.usecase.interactors.fertilizer_llm_recommend_interactor import FertilizerLLMRecommendInteractor, FertilizerRecommendRequestDTO

class _FakeInteractor(FertilizerLLMRecommendInteractor):
    def __init__(self, plan):
        self._plan = plan

    async def execute(self, request: FertilizerRecommendRequestDTO):
        return self._plan

def test_cli_outputs_json(tmp_path, fake_gateway_valid, crop_profile_sample):
    # Build a plan via the fake gateway to reuse domain structure
    plan = fake_gateway_valid.recommend(crop_profile_sample)
    controller = FertilizerCliRecommendController(_FakeInteractor(plan))
    parser = controller.create_argument_parser()

    crop_file = tmp_path / "crop.json"
    crop_file.write_text(json.dumps(crop_profile_sample))

    args = parser.parse_args(["recommend", "--crop-file", str(crop_file), "--json"])
    output = controller.handle(args)

    data = json.loads(output)
    assert data["totals"]["N"] == pytest.approx(plan.totals.N)
    assert len(data["applications"]) == len(plan.applications)

