"""CLI controller for crafting crop profiles (adapter layer)."""

import argparse
import asyncio
import json
from typing import Optional

from agrr_core.adapter.gateways.crop_profile_gateway_impl import (
    CropProfileGatewayImpl,
)
from agrr_core.adapter.presenters.crop_profile_craft_presenter import (
    CropProfileCraftPresenter,
)
from agrr_core.usecase.interactors.crop_profile_craft_interactor import (
    CropProfileCraftInteractor,
)
from agrr_core.usecase.dto.crop_profile_craft_request_dto import (
    CropProfileCraftRequestDTO,
)


class CropCliCraftController:
    """CLI controller orchestrating the crop profile craft use case."""

    def __init__(
        self,
        gateway: CropProfileGatewayImpl,
        presenter: CropProfileCraftPresenter,
    ) -> None:
        """Initialize with injected gateway and presenter."""
        self.gateway = gateway
        self.presenter = presenter
        # Instantiate interactor inside controller per project rule
        self.interactor = CropProfileCraftInteractor(
            gateway=self.gateway, presenter=self.presenter
        )

    def create_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Crop Profile CLI - Get crop growth profiles using AI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Get crop profile for tomato (in Japanese)
  agrr crop --query "トマト"
  
  # Get profile for a specific variety
  agrr crop --query "アイコトマト"
  
  # Get profile for rice
  agrr crop --query "稲"
  
  # Save crop profile to file
  agrr crop --query "トマト" > crop_profile.json

Output Format (JSON):
  {
    "crop": {
      "crop_id": "tomato",
      "name": "Tomato",
      "variety": "general",
      "area_per_unit": 0.25,
      "revenue_per_area": 5000.0,
      "max_revenue": 250000.0,
      "groups": ["Solanaceae", "fruiting_vegetables"]
    },
    "stage_requirements": [
      {
        "stage": {"name": "germination", "order": 1},
        "temperature": {
          "base_temperature": 10.0,      // 発育下限温度（これより低いと発育しない）
          "optimal_min": 20.0,            // 最適温度範囲の下限
          "optimal_max": 30.0,            // 最適温度範囲の上限
          "low_stress_threshold": 15.0,  // 低温ストレス閾値
          "high_stress_threshold": 35.0, // 高温ストレス閾値
          "frost_threshold": 2.0,        // 霜害リスク温度
          "max_temperature": 38.0,       // 発育上限温度（これより高いと発育停止）
          "sterility_risk_threshold": 40.0  // 不稔リスク温度（開花期のみ）
        },
        "thermal": {"required_gdd": 150.0},
        "sunshine": {
          "minimum_sunshine_hours": 3.0,
          "target_sunshine_hours": 6.0
        }
      },
      {
        "stage": {"name": "vegetative", "order": 2},
        "temperature": {
          "base_temperature": 10.0,
          "optimal_min": 18.0,
          "optimal_max": 28.0,
          "low_stress_threshold": 13.0,
          "high_stress_threshold": 33.0,
          "frost_threshold": 2.0,
          "max_temperature": 36.0
        },
        "thermal": {"required_gdd": 800.0},
        "sunshine": {
          "minimum_sunshine_hours": 4.0,
          "target_sunshine_hours": 8.0
        }
      }
    ]
  }

Temperature Parameters Explained:
  base_temperature       - Lower threshold: no growth below this (GDD = 0)
  optimal_min/max        - Optimal temperature range for best growth
  low_stress_threshold   - Low temperature stress begins
  high_stress_threshold  - High temperature stress begins
  frost_threshold        - Frost damage risk temperature
  max_temperature        - Upper threshold: no growth above this (GDD = 0)
  sterility_risk_threshold - Sterility risk (flowering stage only, optional)

Temperature constraints:
  base_temperature < optimal_min ≤ optimal_max < max_temperature

Note: This command uses AI (LLM) to generate crop growth profiles.
      The output format is ready to use directly with 'agrr progress' and 'agrr optimize-period' commands.
            """
        )

        parser.add_argument(
            "--query",
            "-q",
            required=True,
            help='Crop query string (e.g., "トマト", "アイコトマト", "稲")',
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output as JSON (default: True)",
        )

        return parser

    async def handle_craft_command(self, args) -> None:
        request = CropProfileCraftRequestDTO(crop_query=args.query)
        result = await self.interactor.execute(request)

        # Always print JSON; the presenter already wraps success/error
        print(json.dumps(result, ensure_ascii=False))

    async def run(self, args: Optional[list] = None) -> None:
        parser = self.create_argument_parser()
        parsed_args = parser.parse_args(args)

        # No subcommands - directly handle the craft command
        await self.handle_craft_command(parsed_args)


