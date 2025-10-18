"""CLI controller for allocation adjustment (adapter layer)."""

import argparse
import asyncio
from datetime import datetime
from typing import Optional

from agrr_core.usecase.gateways.allocation_result_gateway import AllocationResultGateway
from agrr_core.usecase.gateways.move_instruction_gateway import MoveInstructionGateway
from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.usecase.interactors.allocation_adjust_interactor import AllocationAdjustInteractor
from agrr_core.usecase.dto.allocation_adjust_request_dto import AllocationAdjustRequestDTO
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.adapter.presenters.allocation_adjust_cli_presenter import (
    AllocationAdjustCliPresenter,
)


class AllocationAdjustCliController:
    """CLI controller for allocation adjustment."""
    
    def __init__(
        self,
        allocation_result_gateway: AllocationResultGateway,
        move_instruction_gateway: MoveInstructionGateway,
        field_gateway: FieldGateway,
        crop_gateway: CropProfileGateway,
        weather_gateway: WeatherGateway,
        crop_profile_gateway_internal: CropProfileGateway,
        presenter: AllocationAdjustCliPresenter,
        interaction_rule_gateway: Optional[InteractionRuleGateway] = None,
        config: Optional[OptimizationConfig] = None,
    ):
        """Initialize with injected dependencies.
        
        Args:
            allocation_result_gateway: Gateway for loading current allocation result
            move_instruction_gateway: Gateway for loading move instructions
            field_gateway: Gateway for field operations
            crop_gateway: Gateway for crop operations
            weather_gateway: Gateway for weather data operations
            crop_profile_gateway_internal: Internal gateway for growth period optimization
            presenter: Presenter for output formatting
            interaction_rule_gateway: Optional gateway for interaction rules
            config: Optional optimization configuration
        """
        self.allocation_result_gateway = allocation_result_gateway
        self.move_instruction_gateway = move_instruction_gateway
        self.field_gateway = field_gateway
        self.crop_gateway = crop_gateway
        self.weather_gateway = weather_gateway
        self.crop_profile_gateway_internal = crop_profile_gateway_internal
        self.presenter = presenter
        self.interaction_rule_gateway = interaction_rule_gateway
        self.config = config or OptimizationConfig()
        
        # Instantiate interactor
        self.interactor = AllocationAdjustInteractor(
            allocation_result_gateway=allocation_result_gateway,
            move_instruction_gateway=move_instruction_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
            interaction_rule_gateway=interaction_rule_gateway,
            config=self.config,
        )
    
    def create_argument_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for adjust command."""
        parser = argparse.ArgumentParser(
            description="Allocation Adjustment - Adjust existing allocation based on move instructions",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic adjustment
  agrr optimize adjust \\
    --current-allocation current_allocation.json \\
    --moves moves.json \\
    --weather-file weather.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31

  # With fields and crops override
  agrr optimize adjust \\
    --current-allocation current_allocation.json \\
    --moves moves.json \\
    --weather-file weather.json \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31

  # With interaction rules
  agrr optimize adjust \\
    --current-allocation current_allocation.json \\
    --moves moves.json \\
    --weather-file weather.json \\
    --interaction-rules-file interaction_rules.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31

  # With JSON output
  agrr optimize adjust \\
    --current-allocation current_allocation.json \\
    --moves moves.json \\
    --weather-file weather.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --format json

Input Files:

1. Current Allocation File (JSON):
   Output from 'agrr optimize allocate' command:
   {
     "optimization_result": {
       "optimization_id": "opt_001",
       "field_schedules": [...],
       "total_profit": 150000.0
     }
   }

2. Moves File (JSON):
   {
     "moves": [
       {
         "allocation_id": "alloc_001",
         "action": "move",
         "to_field_id": "field_2",
         "to_start_date": "2024-05-15",
         "to_area": 12.0
       },
       {
         "allocation_id": "alloc_002",
         "action": "remove"
       }
     ]
   }

Move Actions:
  - "move": Move allocation to different field, start date, or area
    * Required fields: to_field_id, to_start_date
    * Optional field: to_area (if omitted, uses original area)
  - "remove": Remove allocation from schedule
    * No additional fields required

Notes:
  - After applying moves, the system re-optimizes the remaining allocations
  - All constraints (fallow period, interaction rules) are enforced
  - You can override fields and crops using --fields-file and --crops-file
  - Planning period must cover all allocations in the result
"""
        )
        
        parser.add_argument(
            "--current-allocation",
            "-ca",
            required=True,
            help="Path to current allocation JSON file (output from 'agrr optimize allocate')",
        )
        parser.add_argument(
            "--moves",
            "-m",
            required=True,
            help="Path to move instructions JSON file",
        )
        parser.add_argument(
            "--weather-file",
            "-w",
            required=True,
            help="Path to weather data file (JSON or CSV)",
        )
        parser.add_argument(
            "--planning-start",
            "-s",
            required=True,
            help='Planning period start date in YYYY-MM-DD format (e.g., "2024-04-01")',
        )
        parser.add_argument(
            "--planning-end",
            "-e",
            required=True,
            help='Planning period end date in YYYY-MM-DD format (e.g., "2024-10-31")',
        )
        parser.add_argument(
            "--fields-file",
            "-fs",
            required=False,
            help="Path to fields configuration file (JSON) - overrides fields from current allocation",
        )
        parser.add_argument(
            "--crops-file",
            "-cs",
            required=False,
            help="Path to crops configuration file (JSON) - overrides crops from current allocation",
        )
        parser.add_argument(
            "--interaction-rules-file",
            "-irf",
            required=False,
            help="Path to interaction rules JSON file (optional)",
        )
        parser.add_argument(
            "--objective",
            "-obj",
            choices=["maximize_profit", "minimize_cost"],
            default="maximize_profit",
            help="Optimization objective (default: maximize_profit)",
        )
        parser.add_argument(
            "--max-time",
            "-mt",
            type=float,
            required=False,
            help="Maximum computation time in seconds (optional)",
        )
        parser.add_argument(
            "--format",
            "-fmt",
            choices=["table", "json"],
            default="table",
            help="Output format (default: table)",
        )
        parser.add_argument(
            "--enable-parallel",
            action="store_true",
            help="Enable parallel candidate generation for faster computation",
        )
        parser.add_argument(
            "--disable-local-search",
            action="store_true",
            help="Disable local search (initial allocation only)",
        )
        parser.add_argument(
            "--algorithm",
            "-alg",
            choices=["greedy", "dp"],
            default="dp",
            help="Algorithm for re-optimization: 'dp' (optimal per-field) or 'greedy' (fast heuristic). Default: dp",
        )
        parser.add_argument(
            "--no-filter-redundant",
            action="store_true",
            help="Disable filtering of redundant growth period candidates",
        )
        
        return parser
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f'Invalid date format: "{date_str}". Use YYYY-MM-DD (e.g., "2024-04-01")'
            )
    
    async def handle_adjust_command(self, args) -> None:
        """Handle the adjust command."""
        # Parse planning period dates
        try:
            planning_start = self._parse_date(args.planning_start)
            planning_end = self._parse_date(args.planning_end)
        except ValueError as e:
            print(f"Error: {str(e)}")
            return
        
        # Load move instructions
        try:
            move_instructions = await self.move_instruction_gateway.get_all()
            if not move_instructions:
                print("Error: No move instructions found.")
                return
        except Exception as e:
            print(f"Error loading move instructions: {str(e)}")
            return
        
        # Update presenter format
        self.presenter.output_format = args.format
        
        # Update optimization config
        config = OptimizationConfig()
        if getattr(args, "enable_parallel", False):
            config.enable_parallel_candidate_generation = True
        
        # Create request DTO
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",  # Will be loaded from file
            move_instructions=move_instructions,
            planning_period_start=planning_start,
            planning_period_end=planning_end,
            optimization_objective=args.objective,
            max_computation_time=getattr(args, "max_time", None),
            filter_redundant_candidates=not getattr(args, "no_filter_redundant", False),
        )
        
        # Execute use case
        try:
            enable_local_search = not getattr(args, "disable_local_search", False)
            algorithm = getattr(args, "algorithm", "dp")
            
            response = await self.interactor.execute(
                request,
                enable_local_search=enable_local_search,
                config=config,
                algorithm=algorithm,
            )
            
            self.presenter.present(response)
            
        except Exception as e:
            print(f"Error adjusting allocation: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def run(self, args: Optional[list] = None) -> None:
        """Run the controller with CLI arguments."""
        parser = self.create_argument_parser()
        parsed_args = parser.parse_args(args)
        await self.handle_adjust_command(parsed_args)

