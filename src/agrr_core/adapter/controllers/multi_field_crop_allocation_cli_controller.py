"""CLI controller for multi-field crop allocation optimization (adapter layer)."""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Optional, List

from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.usecase.ports.input.multi_field_crop_allocation_input_port import (
    MultiFieldCropAllocationInputPort,
)
from agrr_core.usecase.ports.output.multi_field_crop_allocation_output_port import (
    MultiFieldCropAllocationOutputPort,
)
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_request_dto import (
    MultiFieldCropAllocationRequestDTO,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_response_dto import (
    MultiFieldCropAllocationResponseDTO,
)
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule


class MultiFieldCropAllocationCliController(MultiFieldCropAllocationInputPort):
    """CLI controller implementing Input Port for multi-field crop allocation optimization."""

    def __init__(
        self,
        field_gateway: FieldGateway,
        crop_gateway: CropProfileGateway,
        weather_gateway: WeatherGateway,
        presenter: MultiFieldCropAllocationOutputPort,
        crop_profile_gateway_internal: CropProfileGateway,
        interaction_rule_gateway: Optional[InteractionRuleGateway] = None,
        config: Optional[OptimizationConfig] = None,
    ) -> None:
        """Initialize with injected dependencies.
        
        Args:
            field_gateway: Gateway for field operations
            crop_gateway: Gateway for crop operations
            weather_gateway: Gateway for weather data operations
            presenter: Presenter for output formatting
            crop_profile_gateway_internal: Internal gateway for crop profile operations in growth period optimization
            interaction_rule_gateway: Optional gateway for loading interaction rules
            config: Optional optimization configuration
            
        Note:
            File paths are NOT passed to Controller/Interactor.
            They are configured at Gateway initialization (done at CLI startup).
            Gateways are already initialized with appropriate repositories and file paths.
        """
        self.field_gateway = field_gateway
        self.crop_gateway = crop_gateway
        self.weather_gateway = weather_gateway
        self.presenter = presenter
        self.interaction_rule_gateway = interaction_rule_gateway
        self.config = config or OptimizationConfig()
        
        # Load interaction rules if gateway is provided
        self.interaction_rules: List[InteractionRule] = []
        
        # Instantiate interactor inside controller
        self.interactor = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=self.field_gateway,
            crop_gateway=self.crop_gateway,
            weather_gateway=self.weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
            config=self.config,
            interaction_rules=self.interaction_rules,
        )

    async def execute(
        self, request: MultiFieldCropAllocationRequestDTO
    ) -> MultiFieldCropAllocationResponseDTO:
        """Execute the multi-field crop allocation optimization use case.
        
        Implementation of Input Port interface.
        
        Args:
            request: Request DTO containing optimization parameters
            
        Returns:
            Response DTO containing optimized allocation result
        """
        return await self.interactor.execute(request)

    def create_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Multi-Field Crop Allocation Optimizer - Optimize crop allocation across multiple fields",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic optimization
  agrr optimize allocate \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json

  # With interaction rules (continuous cultivation impact)
  agrr optimize allocate \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json \\
    --interaction-rules-file interaction_rules.json

  # With JSON output
  agrr optimize allocate \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json --format json

  # With optimization options
  agrr optimize allocate \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json \\
    --objective maximize_profit \\
    --enable-parallel \\
    --max-time 30

  # Use greedy algorithm for faster heuristic allocation
  agrr optimize allocate \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json \\
    --algorithm greedy

  # Test with sample data (different fallow periods per field)
  agrr optimize allocate \\
    --fields-file test_data/allocation_fields_with_fallow.json \\
    --crops-file test_data/allocation_crops_1760447748.json \\
    --planning-start 2023-04-01 --planning-end 2023-10-31 \\
    --weather-file test_data/weather_2023_full.json

  # Test without fallow period (continuous cultivation)
  agrr optimize allocate \\
    --fields-file test_data/allocation_fields_no_fallow.json \\
    --crops-file test_data/allocation_crops_1760447748.json \\
    --planning-start 2023-04-01 --planning-end 2023-10-31 \\
    --weather-file test_data/weather_2023_full.json

Fields File Format (JSON):
  Based on Field entity structure:
  {
    "fields": [
      {
        "field_id": "field_01",           // Required: Unique identifier
        "name": "北圃場",                  // Required: Human-readable name
        "area": 1000.0,                   // Required: Field area in m²
        "daily_fixed_cost": 5000.0,       // Required: Daily fixed cost in ¥/day
        "location": "北区画",              // Optional: Location description
        "fallow_period_days": 28          // Optional: Fallow period in days (default: 28)
      },
      {
        "field_id": "field_02",
        "name": "南圃場",
        "area": 800.0,
        "daily_fixed_cost": 4000.0,
        "fallow_period_days": 14          // Shorter fallow period
      },
      {
        "field_id": "field_03",
        "name": "東圃場",
        "area": 1200.0,
        "daily_fixed_cost": 6000.0
        // fallow_period_days omitted → default 28 days
      }
    ]
  }
  
  Fallow Period:
    - The fallow period is the required rest period for soil recovery between crops
    - Specified in days (integer, >= 0)
    - Default: 28 days if not specified
    - Set to 0 for continuous cultivation (no rest period)
    - Each field can have a different fallow period
    - Example: If crop A finishes on June 30 with 28-day fallow, 
               crop B cannot start before July 28

Crops File Format (JSON):
  {
    "crops": [
      {
        "crop": {
          "crop_id": "rice",
          "name": "Rice",
          "area_per_unit": 0.25,
          "variety": "Koshihikari",
          "revenue_per_area": 30000.0,
          "max_revenue": 1200000.0,
          "groups": ["Poaceae", "grain_crops"]
        },
        "stage_requirements": [
          {
            "stage": {"name": "growth", "order": 1},
            "temperature": {
              "base_temperature": 10.0,
              "optimal_min": 20.0,
              "optimal_max": 30.0,
              "low_stress_threshold": 15.0,
              "high_stress_threshold": 35.0,
              "frost_threshold": 5.0
            },
            "thermal": {"required_gdd": 1500.0},
            "sunshine": {
              "minimum_sunshine_hours": 5.0,
              "target_sunshine_hours": 8.0
            }
          }
        ]
      },
      {
        "crop": {
          "crop_id": "tomato",
          "name": "Tomato",
          "area_per_unit": 0.5,
          "variety": "Momotaro",
          "revenue_per_area": 50000.0,
          "max_revenue": 800000.0,
          "groups": ["Solanaceae", "fruiting_vegetables"]
        },
        "stage_requirements": [
          {
            "stage": {"name": "growth", "order": 1},
            "temperature": {
              "base_temperature": 10.0,
              "optimal_min": 18.0,
              "optimal_max": 28.0,
              "low_stress_threshold": 13.0,
              "high_stress_threshold": 32.0,
              "frost_threshold": 2.0
            },
            "thermal": {"required_gdd": 1200.0},
            "sunshine": {
              "minimum_sunshine_hours": 4.0,
              "target_sunshine_hours": 8.0
            }
          }
        ]
      }
    ]
  }
  
  Note: Each crop entry combines crop info with its growth stage requirements.
        You can generate individual crop profiles using 'agrr crop' command.

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

Interaction Rules File Format (JSON):
  Based on InteractionRule entity structure:
  [
    {
      "rule_id": "rule_001",                    // Required: Unique rule identifier
      "rule_type": "continuous_cultivation",    // Required: Rule type (see below)
      "source_group": "Solanaceae",             // Required: Source group name
      "target_group": "Solanaceae",             // Required: Target group name
      "impact_ratio": 0.7,                      // Required: Impact coefficient
      "is_directional": true,                   // Optional: Default true
      "description": "Continuous Solanaceae reduces revenue by 30%"  // Optional
    },
    {
      "rule_id": "rule_002",
      "rule_type": "beneficial_rotation",
      "source_group": "Fabaceae",
      "target_group": "Poaceae",
      "impact_ratio": 1.1,                      // 1.1 = 10% increase
      "is_directional": true,
      "description": "Legumes to grains increases revenue by 10%"
    },
    {
      "rule_id": "rule_003",
      "rule_type": "companion_planting",
      "source_group": "Solanaceae",
      "target_group": "Lamiaceae",
      "impact_ratio": 1.15,                     // 1.15 = 15% increase
      "is_directional": false,                  // Bidirectional relationship
      "description": "Tomato and basil companion planting"
    }
  ]
  
  Rule Types (RuleType enum):
    - "continuous_cultivation": Continuous cultivation damage (temporal, directed)
    - "beneficial_rotation": Beneficial crop rotation (temporal, directed)
    - "companion_planting": Companion planting (spatial, undirected)
    - "allelopathy": Chemical inhibition between plants (spatial, directed)
    - "soil_compatibility": Soil type compatibility (field-crop, directed)
    - "climate_compatibility": Climate compatibility (field-crop, directed)
  
  Impact Ratio:
    - 1.0 = No impact (neutral)
    - 0.7 = 30% reduction (negative impact)
    - 1.2 = 20% increase (positive impact)
    - 0.0 = Cultivation not possible
  
  Directionality:
    - true: Directed relationship (source → target only)
    - false: Bidirectional relationship (mutual effect)

Output (Table):
  Shows:
  - Optimization summary (algorithm, time, optimality)
  - Financial summary (cost, revenue, profit)
  - Field summary (utilization, crop diversity)
  - Detailed field schedules with allocations

Output (JSON):
  {
    "optimization_result": {
      "optimization_id": "...",
      "total_cost": 1500000,
      "total_revenue": 2500000,
      "total_profit": 1000000,
      "field_schedules": [...]
    },
    "summary": {...}
  }

Notes:
  - Two algorithms available:
    * dp (default): Optimal per-field allocation (DP + Local Search)
    * greedy: Fast heuristic (Greedy + Local Search)
  - DP algorithm solves weighted interval scheduling for each field independently
  - Greedy algorithm is recommended for problems with many crops (6+) and tight revenue constraints
  - Local search is applied by default after initial allocation
  - Weather file can be generated using 'agrr weather' command with --json flag
  - Crop profiles can be generated using 'agrr crop' command
  - Interaction rules allow modeling continuous cultivation impacts
  - The optimizer automatically determines optimal cultivation areas for each crop
            """
        )

        parser.add_argument(
            "--fields-file",
            "-fs",
            required=True,
            help='Path to fields configuration file (JSON)',
        )
        parser.add_argument(
            "--crops-file",
            "-cs",
            required=True,
            help='Path to crops configuration file (JSON)',
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
            "--weather-file",
            "-w",
            required=True,
            help='Path to weather data file (JSON or CSV)',
        )
        parser.add_argument(
            "--objective",
            "-obj",
            choices=["maximize_profit", "minimize_cost"],
            default="maximize_profit",
            help="Optimization objective (default: maximize_profit)",
        )
        parser.add_argument(
            "--interaction-rules-file",
            "-irf",
            required=False,
            help='Path to interaction rules JSON file (optional, for continuous cultivation impact)',
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
            help="Algorithm for initial allocation: 'dp' (optimal per-field) or 'greedy' (fast heuristic). Default: dp",
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
        """Handle the optimize command.
        
        Optimizes crop allocation across multiple fields to maximize profit or minimize cost.
        
        Note:
            File paths are NOT passed to Interactor.
            They are configured at Gateway initialization (done at CLI startup).
            Gateways are already initialized with appropriate repositories and file paths.
        """
        # Parse planning period dates
        try:
            planning_start = self._parse_date(args.planning_start)
            planning_end = self._parse_date(args.planning_end)
        except ValueError as e:
            print(f'Error: {str(e)}')
            return

        # Load fields from gateway
        try:
            fields = await self.field_gateway.get_all()
            if not fields:
                print('Error: No fields found. Make sure --fields-file is a valid fields JSON file.')
                return
            field_ids = [field.field_id for field in fields]
        except Exception as e:
            print(f'Error loading fields: {str(e)}')
            return

        # Load interaction rules if gateway is provided
        if self.interaction_rule_gateway:
            try:
                interaction_rules = await self.interaction_rule_gateway.get_rules()
                # Update interactor with loaded rules
                self.interactor.interaction_rule_service.rules = interaction_rules
            except Exception as e:
                print(f'Warning: Failed to load interaction rules: {str(e)}')
                print('Continuing without interaction rules...')

        # Update presenter format
        self.presenter.output_format = args.format

        # Update optimization config
        config = OptimizationConfig()
        if getattr(args, 'enable_parallel', False):
            config.enable_parallel_candidate_generation = True
        
        # Create request DTO
        # Note: crops are loaded by Interactor via CropProfileGateway
        request = MultiFieldCropAllocationRequestDTO(
            field_ids=field_ids,
            planning_period_start=planning_start,
            planning_period_end=planning_end,
            optimization_objective=args.objective,
            max_computation_time=getattr(args, 'max_time', None),
        )

        # Execute use case
        try:
            enable_local_search = not getattr(args, 'disable_local_search', False)
            algorithm = getattr(args, 'algorithm', 'dp')
            
            response = await self.interactor.execute(
                request,
                enable_local_search=enable_local_search,
                config=config,
                algorithm=algorithm,
            )
            self.presenter.present(response)
        except Exception as e:
            print(f"Error optimizing crop allocation: {str(e)}")
            import traceback
            traceback.print_exc()

    async def run(self, args: Optional[list] = None) -> None:
        """Run the controller with CLI arguments."""
        parser = self.create_argument_parser()
        parsed_args = parser.parse_args(args)

        # No subcommands - directly handle the optimize command
        await self.handle_optimize_command(parsed_args)

