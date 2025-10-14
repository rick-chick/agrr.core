"""CLI controller for optimal growth period calculation (adapter layer)."""

import argparse
import asyncio
from datetime import datetime
from typing import Optional, List

from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.optimization_result_gateway import (
    OptimizationResultGateway,
)
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.ports.input.growth_period_optimize_input_port import (
    GrowthPeriodOptimizeInputPort,
)
from agrr_core.usecase.ports.output.growth_period_optimize_output_port import (
    GrowthPeriodOptimizeOutputPort,
)
from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
    GrowthPeriodOptimizeInteractor,
)
from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    OptimalGrowthPeriodResponseDTO,
)
from agrr_core.usecase.interfaces.weather_interpolator import WeatherInterpolator


class GrowthPeriodOptimizeCliController(GrowthPeriodOptimizeInputPort):
    """CLI controller implementing Input Port for optimal growth period calculation."""

    def __init__(
        self,
        crop_profile_gateway: CropProfileGateway,
        weather_gateway: WeatherGateway,
        presenter: GrowthPeriodOptimizeOutputPort,
        field: Optional['Field'] = None,
        interaction_rule_gateway: Optional[InteractionRuleGateway] = None,
        weather_interpolator: Optional[WeatherInterpolator] = None,
    ) -> None:
        """Initialize with injected dependencies.
        
        Args:
            crop_profile_gateway: Gateway for crop profile operations
            weather_gateway: Gateway for weather data operations
            presenter: Presenter for output formatting
            field: Field entity (read from field config file)
            interaction_rule_gateway: Optional gateway for loading interaction rules
            weather_interpolator: Optional interpolator for missing weather data
        """
        self.crop_profile_gateway = crop_profile_gateway
        self.weather_gateway = weather_gateway
        self.presenter = presenter
        self.field = field
        self.interaction_rule_gateway = interaction_rule_gateway
        self.weather_interpolator = weather_interpolator
        
        # Instantiate interactor inside controller
        self.interactor = GrowthPeriodOptimizeInteractor(
            crop_profile_gateway=self.crop_profile_gateway,
            weather_gateway=self.weather_gateway,
            optimization_result_gateway=None,  # No persistence in CLI
            interaction_rule_gateway=self.interaction_rule_gateway,
            weather_interpolator=self.weather_interpolator,
        )

    async def execute(
        self, request: OptimalGrowthPeriodRequestDTO
    ) -> OptimalGrowthPeriodResponseDTO:
        """Execute the optimal growth period calculation use case.
        
        Implementation of Input Port interface.
        
        Args:
            request: Request DTO containing calculation parameters
            
        Returns:
            Response DTO containing optimal growth period data
        """
        return await self.interactor.execute(request)

    def create_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Optimal Growth Period Calculator - Find the best cultivation start date to minimize costs",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Step 1: Generate crop profile
  agrr crop --query "rice Koshihikari" > rice_profile.json

  # Step 2: Find optimal planting date for rice
  agrr optimize period --crop-file rice_profile.json \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \\
    --weather-file weather.json --field-file field_01.json

  # Find optimal date with JSON output
  agrr optimize period --crop-file tomato_profile.json \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-08-31 \\
    --weather-file weather.json --field-file field_01.json --format json

  # Find optimal date considering continuous cultivation impact
  agrr optimize period --crop-file tomato_profile.json \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-08-31 \\
    --weather-file weather.json --field-file field_01.json \\
    --interaction-rules-file interaction_rules.json


Weather File Format (JSON):
  {
    "latitude": 35.6762,
    "longitude": 139.6503,
    "data": [
      {
        "time": "2024-04-01",
        "temperature_2m_max": 18.5,
        "temperature_2m_min": 8.2,
        "temperature_2m_mean": 13.3
      }
    ]
  }

Field Configuration File Format (JSON):
  {
    "field_id": "field_01",
    "name": "北圃場",
    "area": 1000.0,
    "daily_fixed_cost": 5000.0,
    "location": "北区画"
  }

Crop Profile File Format (JSON):
  {
    "crop": {
      "crop_id": "rice",
      "name": "Rice",
      "variety": "Koshihikari",
      "area_per_unit": 0.25,
      "revenue_per_area": 10000.0,
      "max_revenue": 500000.0,
      "groups": ["Poaceae", "cereals"]
    },
    "stage_requirements": [
      {
        "stage": {"name": "germination", "order": 1},
        "temperature": {
          "base_temperature": 10.0,
          "optimal_min": 20.0,
          "optimal_max": 30.0,
          "low_stress_threshold": 15.0,
          "high_stress_threshold": 35.0,
          "frost_threshold": 0.0
        },
        "thermal": {"required_gdd": 200.0},
        "sunshine": {
          "minimum_sunshine_hours": 3.0,
          "target_sunshine_hours": 6.0
        }
      }
    ]
  }

Output (Table):
  Start Date  | Completion  | Days | GDD    | Cost      | Status
  ------------|-------------|------|--------|-----------|--------
  2024-04-15  | 2024-09-18  | 156  | 2400.0 | ¥780,000  | ★
  2024-04-20  | 2024-09-22  | 155  | 2400.0 | ¥775,000  |

Output (JSON):
  {
    "optimal_result": {
      "start_date": "2024-04-15",
      "completion_date": "2024-09-18",
      "growth_days": 156,
      "total_cost": 780000,
      "accumulated_gdd": 2400.0
    },
    "all_candidates": [ ... ]
  }

Notes:
  - The algorithm evaluates all possible start dates within the evaluation period
  - Only candidates that complete before the evaluation-end deadline are considered
  - The optimal start date minimizes total cultivation cost
  - Daily cost includes fixed costs like field rent, but not variable costs
  - Weather file can be generated using 'agrr weather' command with --json flag
  - Crop profile file must be generated first using 'agrr crop' command
  - The output from 'agrr crop' can be used directly as --crop-file input
  - The 'groups' field in crop data is essential for interaction rules (continuous cultivation, etc.)
            """
        )

        parser.add_argument(
            "--crop-file",
            "-c",
            required=True,
            help='Path to crop profile file (JSON, generated by "agrr crop")',
        )
        parser.add_argument(
            "--evaluation-start",
            "-s",
            required=True,
            help='Earliest possible start date in YYYY-MM-DD format (e.g., "2024-04-01")',
        )
        parser.add_argument(
            "--evaluation-end",
            "-e",
            required=True,
            help='Completion deadline in YYYY-MM-DD format - cultivation must finish by this date (e.g., "2024-06-30")',
        )
        parser.add_argument(
            "--weather-file",
            "-w",
            required=True,
            help='Path to weather data file (JSON or CSV)',
        )
        parser.add_argument(
            "--field-file",
            "-f",
            required=True,
            help='Path to field configuration file (JSON containing field information including daily_fixed_cost)',
        )
        parser.add_argument(
            "--interaction-rules-file",
            "-irf",
            required=False,
            help='Path to interaction rules JSON file (optional, for continuous cultivation impact)',
        )
        parser.add_argument(
            "--format",
            "-fmt",
            choices=["table", "json"],
            default="table",
            help="Output format (default: table)",
        )

        return parser

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object.
        
        Args:
            date_str: Date string (e.g., "2024-04-01")
            
        Returns:
            datetime object
            
        Raises:
            ValueError: If date format is invalid
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f'Invalid date format: "{date_str}". Use YYYY-MM-DD (e.g., "2024-04-01")'
            )

    async def handle_period_command(self, args) -> None:
        """Handle the period optimization command.
        
        Finds the optimal cultivation start date that:
        - Starts on or after evaluation_start
        - Completes by evaluation_end (deadline)
        - Minimizes total cost
        """
        # Parse evaluation period dates
        try:
            evaluation_start = self._parse_date(args.evaluation_start)
            evaluation_end = self._parse_date(args.evaluation_end)
        except ValueError as e:
            print(f'Error: {str(e)}')
            return

        # Update presenter format
        self.presenter.output_format = args.format

        # Check if field entity was loaded
        if not self.field:
            print('Error: Field configuration not loaded. Make sure --field-file is a valid field JSON file.')
            return
        
        # Load crop profile from file
        try:
            from agrr_core.adapter.repositories.crop_profile_file_repository import CropProfileFileRepository
            from agrr_core.framework.repositories.file_repository import FileRepository
            file_repo = FileRepository()
            profile_repo = CropProfileFileRepository(file_repository=file_repo, file_path=args.crop_file)
            crop_profile = await profile_repo.get()
        except Exception as e:
            print(f"Error loading crop profile from {args.crop_file}: {str(e)}")
            return
        
        # Note: File paths are NOT passed to Interactor
        # They are configured at Gateway initialization (done at CLI startup)
        # Gateways are already initialized with appropriate repositories and file paths
        
        # Create request DTO (no file paths, no entities - just business data)
        request = OptimalGrowthPeriodRequestDTO(
            crop_id=crop_profile.crop.crop_id,
            variety=crop_profile.crop.variety,
            evaluation_period_start=evaluation_start,
            evaluation_period_end=evaluation_end,
            field=self.field,
        )

        # Execute use case
        try:
            response = await self.execute(request)
            self.presenter.present(response)
        except Exception as e:
            print(f"Error calculating optimal growth period: {str(e)}")
            import traceback
            traceback.print_exc()

    async def run(self, args: Optional[list] = None) -> None:
        """Run the controller with CLI arguments."""
        parser = self.create_argument_parser()
        parsed_args = parser.parse_args(args)

        # No subcommands - directly handle the period optimization
        await self.handle_period_command(parsed_args)

