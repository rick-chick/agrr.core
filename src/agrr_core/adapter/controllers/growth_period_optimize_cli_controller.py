"""CLI controller for optimal growth period calculation (adapter layer)."""

import argparse
import asyncio
from datetime import datetime
from typing import Optional, List

from agrr_core.usecase.gateways.crop_requirement_gateway import CropRequirementGateway
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
        crop_requirement_gateway: CropRequirementGateway,
        weather_gateway: WeatherGateway,
        presenter: GrowthPeriodOptimizeOutputPort,
        field: Optional['Field'] = None,
        optimization_result_gateway: Optional[OptimizationResultGateway] = None,
        interaction_rule_gateway: Optional[InteractionRuleGateway] = None,
        weather_interpolator: Optional[WeatherInterpolator] = None,
    ) -> None:
        """Initialize with injected dependencies.
        
        Args:
            crop_requirement_gateway: Gateway for crop requirement operations
            weather_gateway: Gateway for weather data operations
            presenter: Presenter for output formatting
            field: Field entity (read from field config file)
            optimization_result_gateway: Optional gateway for saving optimization results
            interaction_rule_gateway: Optional gateway for loading interaction rules
            weather_interpolator: Optional interpolator for missing weather data
        """
        self.crop_requirement_gateway = crop_requirement_gateway
        self.weather_gateway = weather_gateway
        self.presenter = presenter
        self.field = field
        self.optimization_result_gateway = optimization_result_gateway
        self.interaction_rule_gateway = interaction_rule_gateway
        self.weather_interpolator = weather_interpolator
        
        # Instantiate interactor inside controller
        self.interactor = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=self.crop_requirement_gateway,
            weather_gateway=self.weather_gateway,
            optimization_result_gateway=self.optimization_result_gateway,
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
  # Find optimal planting date for rice
  agrr optimize-period optimize --crop rice --variety Koshihikari \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \\
    --weather-file weather.json --field-config field_01.json

  # Find optimal date with JSON output
  agrr optimize-period optimize --crop tomato \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-08-31 \\
    --weather-file weather.json --field-config field_01.json --format json

  # Find optimal date considering continuous cultivation impact
  agrr optimize-period optimize --crop tomato \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-08-31 \\
    --weather-file weather.json --field-config field_01.json \\
    --interaction-rules interaction_rules.json

  # Save optimization results for later analysis
  agrr optimize-period optimize --crop rice --variety Koshihikari \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \\
    --weather-file weather.json --field-config field_01.json --save-results

  # List all saved optimization results
  agrr optimize-period list-results

  # Show details of a saved result
  agrr optimize-period show-result rice_Koshihikari_2024-04-01_2024-09-30

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

Crop Requirement File Format (JSON, optional):
  {
    "crop_name": "rice",
    "variety": "Koshihikari",
    "base_temperature": 10.0,
    "gdd_requirement": 2400.0,
    "stages": [
      {
        "name": "germination",
        "gdd_requirement": 200.0,
        "optimal_temp_min": 20.0,
        "optimal_temp_max": 30.0
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
  - Weather file can be generated using 'agrr weather' command
  - Crop requirements are auto-generated using AI if not provided
            """
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        optimize_parser = subparsers.add_parser(
            "optimize", 
            help="Find optimal start date that minimizes cost while meeting completion deadline"
        )
        optimize_parser.add_argument(
            "--crop",
            "-c",
            required=True,
            help='Crop name (e.g., "rice", "tomato")',
        )
        optimize_parser.add_argument(
            "--variety",
            "-v",
            help='Variety/cultivar (e.g., "Koshihikari")',
        )
        optimize_parser.add_argument(
            "--evaluation-start",
            "-s",
            required=True,
            help='Earliest possible start date in YYYY-MM-DD format (e.g., "2024-04-01")',
        )
        optimize_parser.add_argument(
            "--evaluation-end",
            "-e",
            required=True,
            help='Completion deadline in YYYY-MM-DD format - cultivation must finish by this date (e.g., "2024-06-30")',
        )
        optimize_parser.add_argument(
            "--weather-file",
            "-w",
            required=True,
            help='Path to weather data file (JSON or CSV)',
        )
        optimize_parser.add_argument(
            "--crop-requirement-file",
            "-r",
            required=False,
            help='Path to crop requirement file (JSON). If not provided, will use LLM to generate requirements.',
        )
        optimize_parser.add_argument(
            "--field-config",
            "-fc",
            required=True,
            help='Path to field configuration file (JSON containing field information including daily_fixed_cost)',
        )
        optimize_parser.add_argument(
            "--interaction-rules",
            "-ir",
            required=False,
            help='Path to interaction rules JSON file (optional, for continuous cultivation impact)',
        )
        optimize_parser.add_argument(
            "--format",
            "-fmt",
            choices=["table", "json"],
            default="table",
            help="Output format (default: table)",
        )
        optimize_parser.add_argument(
            "--save-results",
            action="store_true",
            help="Save intermediate optimization results for later analysis",
        )

        # Add 'list-results' subcommand
        list_parser = subparsers.add_parser(
            "list-results",
            help="List all saved optimization results"
        )
        list_parser.add_argument(
            "--format",
            "-fmt",
            choices=["table", "json"],
            default="table",
            help="Output format (default: table)",
        )

        # Add 'show-result' subcommand
        show_parser = subparsers.add_parser(
            "show-result",
            help="Show details of a specific optimization result"
        )
        show_parser.add_argument(
            "optimization_id",
            help="Optimization ID to show (format: crop_variety_startdate_enddate)",
        )
        show_parser.add_argument(
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

    async def handle_optimize_command(self, args) -> None:
        """Handle the optimize calculation command.
        
        Finds the optimal cultivation start date that:
        - Starts on or after evaluation_start
        - Completes by evaluation_end (deadline)
        - Minimizes total cost
        """
        # Check if saving results is requested but gateway is not available
        if getattr(args, 'save_results', False) and self.optimization_result_gateway is None:
            print("Warning: --save-results specified but optimization result storage is not enabled.")
            print("Results will be calculated but not saved.")
        
        # Parse evaluation period dates
        try:
            evaluation_start = self._parse_date(args.evaluation_start)
            evaluation_end = self._parse_date(args.evaluation_end)
        except ValueError as e:
            print(f'Error: {str(e)}')
            return

        # Update presenter format
        self.presenter.output_format = args.format

        # Validate that field-config is provided
        if not getattr(args, 'field_config', None):
            print('Error: --field-config is required')
            return
        
        # Check if field entity was loaded
        if not self.field:
            print('Error: Field configuration not loaded. Make sure --field-config is a valid field JSON file.')
            return
        
        # Create request DTO
        request = OptimalGrowthPeriodRequestDTO(
            crop_id=args.crop,
            variety=args.variety,
            evaluation_period_start=evaluation_start,
            evaluation_period_end=evaluation_end,
            weather_data_file=args.weather_file,
            field=self.field,
            crop_requirement_file=getattr(args, 'crop_requirement_file', None),
            interaction_rules_file=getattr(args, 'interaction_rules', None),
        )

        # Execute use case
        try:
            response = await self.execute(request)
            self.presenter.present(response)
            
            # Show saved message if results were saved
            if getattr(args, 'save_results', False) and self.optimization_result_gateway is not None:
                optimization_id = f"{args.crop}_{args.variety or 'default'}_{evaluation_start.date()}_{evaluation_end.date()}"
                print(f"\n✓ Results saved with ID: {optimization_id}")
                print(f"  Use 'agrr optimize-period show-result {optimization_id}' to view saved results")
        except Exception as e:
            print(f"Error calculating optimal growth period: {str(e)}")
            import traceback
            traceback.print_exc()

    async def handle_list_results_command(self, args) -> None:
        """Handle the list-results command."""
        if self.optimization_result_gateway is None:
            print("Error: Optimization result storage is not enabled.")
            return
        
        try:
            all_results = await self.optimization_result_gateway.get_all()
            
            if not all_results:
                print("No saved optimization results found.")
                return
            
            if args.format == "json":
                import json
                results_data = [
                    {"optimization_id": opt_id, "num_candidates": len(results)}
                    for opt_id, results in all_results
                ]
                print(json.dumps(results_data, indent=2))
            else:
                # Table format
                print("\n" + "="*80)
                print("Saved Optimization Results")
                print("="*80)
                print(f"{'Optimization ID':<50} {'Candidates':<10}")
                print("-"*80)
                for opt_id, results in all_results:
                    print(f"{opt_id:<50} {len(results):<10}")
                print("="*80)
                print(f"\nTotal: {len(all_results)} optimization result(s)")
                print("\nUse 'agrr optimize-period show-result <optimization_id>' to view details")
        except Exception as e:
            print(f"Error listing optimization results: {str(e)}")
            import traceback
            traceback.print_exc()

    async def handle_show_result_command(self, args) -> None:
        """Handle the show-result command."""
        if self.optimization_result_gateway is None:
            print("Error: Optimization result storage is not enabled.")
            return
        
        try:
            results = await self.optimization_result_gateway.get(args.optimization_id)
            
            if results is None:
                print(f"No optimization result found with ID: {args.optimization_id}")
                return
            
            if args.format == "json":
                import json
                results_data = [
                    {
                        "start_date": r.start_date.isoformat(),
                        "completion_date": r.completion_date.isoformat() if r.completion_date else None,
                        "growth_days": r.growth_days,
                        "accumulated_gdd": r.accumulated_gdd,
                        "total_cost": r.total_cost,
                        "is_optimal": r.is_optimal,
                        "base_temperature": r.base_temperature,
                    }
                    for r in results
                ]
                print(json.dumps(results_data, indent=2))
            else:
                # Table format
                print("\n" + "="*100)
                print(f"Optimization Result: {args.optimization_id}")
                print("="*100)
                print(f"{'Start Date':<12} {'Completion':<12} {'Days':<6} {'GDD':<10} {'Cost':<12} {'Optimal':<8}")
                print("-"*100)
                for r in results:
                    completion = r.completion_date.strftime("%Y-%m-%d") if r.completion_date else "N/A"
                    days = str(r.growth_days) if r.growth_days else "N/A"
                    cost_str = f"¥{r.total_cost:,.0f}" if r.total_cost else "N/A"
                    optimal_mark = "★" if r.is_optimal else ""
                    print(f"{r.start_date.strftime('%Y-%m-%d'):<12} {completion:<12} {days:<6} "
                          f"{r.accumulated_gdd:<10.1f} {cost_str:<12} {optimal_mark:<8}")
                print("="*100)
                print(f"\nTotal candidates: {len(results)}")
                optimal_count = sum(1 for r in results if r.is_optimal)
                if optimal_count > 0:
                    print(f"Optimal candidates: {optimal_count} (marked with ★)")
        except Exception as e:
            print(f"Error showing optimization result: {str(e)}")
            import traceback
            traceback.print_exc()

    async def run(self, args: Optional[list] = None) -> None:
        """Run the controller with CLI arguments."""
        parser = self.create_argument_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.command:
            parser.print_help()
            return

        if parsed_args.command == "optimize":
            await self.handle_optimize_command(parsed_args)
        elif parsed_args.command == "list-results":
            await self.handle_list_results_command(parsed_args)
        elif parsed_args.command == "show-result":
            await self.handle_show_result_command(parsed_args)
        else:
            parser.print_help()

