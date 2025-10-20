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
        """
        self.allocation_result_gateway = allocation_result_gateway
        self.move_instruction_gateway = move_instruction_gateway
        self.field_gateway = field_gateway
        self.crop_gateway = crop_gateway
        self.weather_gateway = weather_gateway
        self.crop_profile_gateway_internal = crop_profile_gateway_internal
        self.presenter = presenter
        self.interaction_rule_gateway = interaction_rule_gateway
        
        # Instantiate interactor
        self.interactor = AllocationAdjustInteractor(
            allocation_result_gateway=allocation_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
            interaction_rule_gateway=interaction_rule_gateway,
        )
    
    def create_argument_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for adjust command."""
        parser = argparse.ArgumentParser(
            description="Allocation Adjustment - Adjust existing allocation based on move instructions",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 WORKFLOW: How to Use This Command
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Run initial optimization (if not done yet)
  agrr optimize allocate \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json \\
    --format json > current_allocation.json

Step 2: Create a moves file (moves.json)
  Specify which allocations to move, remove, or add.
  See "Moves File Format" section below for details.

Step 3: Run adjustment
  agrr optimize adjust \\
    --current-allocation current_allocation.json \\
    --moves moves.json \\
    --weather-file weather.json \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31

  ⚠️ Important: Use the SAME files from Step 1:
    - Same fields.json
    - Same crops.json
    - Same weather.json
    - Same planning-start and planning-end dates

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example 1: Basic adjustment
  agrr optimize adjust \\
    --current-allocation current_allocation.json \\
    --moves moves.json \\
    --weather-file weather.json \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31

Example 2: With interaction rules
  agrr optimize adjust \\
    --current-allocation current_allocation.json \\
    --moves moves.json \\
    --weather-file weather.json \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --interaction-rules-file interaction_rules.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31

Example 3: With JSON output (for further processing)
  agrr optimize adjust \\
    --current-allocation current_allocation.json \\
    --moves moves.json \\
    --weather-file weather.json \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --format json > adjusted_allocation.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 INPUT FILE FORMATS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Current Allocation File (JSON):
   Output from 'agrr optimize allocate' command:
   {
     "optimization_result": {
       "optimization_id": "opt_001",
       "field_schedules": [
         {
           "field_id": "field_1",
           "field_name": "Field 1",
           "allocations": [
             {
               "allocation_id": "alloc_001",        // <- Use this ID in moves file
               "crop_id": "tomato",
               "crop_name": "Tomato",
               "variety": "Momotaro",
               "area_used": 500.0,                  // <- Required: Area in m²
               "start_date": "2024-05-01",
               "completion_date": "2024-08-15",
               "growth_days": 106,
               "accumulated_gdd": 1520.5,
               "total_cost": 530000,
               "expected_revenue": 750000,
               "profit": 220000
             }
           ]
         }
       ],
       "total_profit": 150000.0
     }
   }
   
   ⚠️ Note: The 'area_used' field in each allocation is required.
             Use the exact JSON output from 'agrr optimize allocate --format json'

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
       },
       {
         "action": "add",
         "crop_id": "tomato",
         "to_field_id": "field_1",
         "to_start_date": "2024-06-01",
         "to_area": 15.0
       }
     ]
   }

Move Actions:
  - "move": Move allocation to different field, start date, or area
    * Required fields: allocation_id, to_field_id, to_start_date
    * Optional field: to_area (if omitted, uses original area)
  - "remove": Remove allocation from schedule
    * Required fields: allocation_id
  - "add": Add new crop allocation
    * Required fields: crop_id, to_field_id, to_start_date, to_area
    * Optional field: variety (if omitted, uses default variety from crops file)
    * Note: allocation_id is not needed for "add" action

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Table Format (default):
  - Shows before/after comparison
  - Displays applied moves
  - Shows adjusted field schedules
  - Financial summary (cost, revenue, profit)

JSON Format (--format json):
  - Same structure as 'agrr optimize allocate' output
  - Can be used as input for another 'agrr optimize adjust' call
  - Suitable for automation and further processing
  - Shows updated cost, revenue, and profit for adjusted allocations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 WHAT THIS COMMAND DOES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Loads existing allocation result
2. Applies your move instructions (move/remove/add allocations)
3. For moved allocations:
   - Calculates completion date from new start date using GDD calculation
   - Recalculates cost, revenue, and profit for affected fields
4. For added allocations:
   - Creates new crop allocation from crops file
   - Calculates completion date using GDD calculation
   - Calculates cost, revenue, and profit
5. Validates all constraints (fallow period, interaction rules, etc.)

Use Cases:
  - Manual correction of automated allocation results
  - What-if analysis (test different scenarios)
  - Fixing constraint violations discovered after optimization
  - Adjusting allocation based on real-world changes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ COMMON ERRORS & SOLUTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Error: "KeyError: 'area_used'"
  Solution: Make sure current_allocation.json is from 'agrr optimize allocate --format json'
            Do NOT create the file manually or edit it.

Error: "allocation_id not found"
  Solution: Check that allocation IDs in moves.json exist in current_allocation.json
            Use exact IDs from the "allocations" array in field_schedules.

Error: "Invalid date format"
  Solution: Use YYYY-MM-DD format for to_start_date in moves.json
            Example: "2024-05-15", not "05/15/2024"

Error: "Field not found"
  Solution: Make sure to_field_id in moves.json matches a field_id in fields.json
            Use exact same fields.json as original optimization.

Error: "Time overlap with allocation ... (considering X-day fallow period)"
  Solution: The target field has existing allocations. Choose a different:
            - Start date (avoid overlap + fallow period)
            - Target field (check field availability using command above)
            Or remove conflicting allocations first.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 RELATED COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  agrr optimize allocate --help    Create initial allocation
  agrr optimize period --help      Optimize planting date for single crop

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
            required=True,
            help="Path to fields configuration file (JSON) - required for GDD calculation",
        )
        parser.add_argument(
            "--crops-file",
            "-cs",
            required=True,
            help="Path to crops configuration file (JSON) - required for GDD calculation (must include stage_requirements)",
        )
        parser.add_argument(
            "--interaction-rules-file",
            "-irf",
            required=False,
            help="Path to interaction rules JSON file (optional)",
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
        
        # Create request DTO
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",  # Will be loaded from file
            move_instructions=move_instructions,
            planning_period_start=planning_start,
            planning_period_end=planning_end,
        )
        
        # Execute use case
        try:
            response = await self.interactor.execute(request)
            
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

