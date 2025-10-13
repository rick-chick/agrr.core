"""CLI controller for multi-field crop allocation optimization (adapter layer)."""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Optional, List

from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.usecase.gateways.crop_requirement_gateway import CropRequirementGateway
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
    CropRequirementSpec,
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
        crop_requirement_gateway: CropRequirementGateway,
        weather_gateway: WeatherGateway,
        presenter: MultiFieldCropAllocationOutputPort,
        interaction_rule_gateway: Optional[InteractionRuleGateway] = None,
        config: Optional[OptimizationConfig] = None,
    ) -> None:
        """Initialize with injected dependencies.
        
        Args:
            field_gateway: Gateway for field operations
            crop_requirement_gateway: Gateway for crop requirement operations
            weather_gateway: Gateway for weather data operations
            presenter: Presenter for output formatting
            interaction_rule_gateway: Optional gateway for loading interaction rules
            config: Optional optimization configuration
        """
        self.field_gateway = field_gateway
        self.crop_requirement_gateway = crop_requirement_gateway
        self.weather_gateway = weather_gateway
        self.presenter = presenter
        self.interaction_rule_gateway = interaction_rule_gateway
        self.config = config or OptimizationConfig()
        
        # Load interaction rules if gateway is provided
        self.interaction_rules: List[InteractionRule] = []
        
        # Instantiate interactor inside controller
        self.interactor = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=self.field_gateway,
            crop_requirement_gateway=self.crop_requirement_gateway,
            weather_gateway=self.weather_gateway,
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
  agrr allocate optimize \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json

  # With interaction rules (continuous cultivation impact)
  agrr allocate optimize \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json \\
    --interaction-rules-file interaction_rules.json

  # With JSON output
  agrr allocate optimize \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json --format json

  # With optimization options
  agrr allocate optimize \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json \\
    --objective maximize_profit \\
    --enable-parallel \\
    --max-time 30

Fields File Format (JSON):
  Based on Field entity structure:
  {
    "fields": [
      {
        "field_id": "field_01",           // Required: Unique identifier
        "name": "北圃場",                  // Required: Human-readable name
        "area": 1000.0,                   // Required: Field area in m²
        "daily_fixed_cost": 5000.0,       // Required: Daily fixed cost in ¥/day
        "location": "北区画"               // Optional: Location description
      },
      {
        "field_id": "field_02",
        "name": "南圃場",
        "area": 800.0,
        "daily_fixed_cost": 4000.0
      }
    ]
  }

Crops File Format (JSON):
  Based on Crop entity structure (extended with optimization parameters):
  {
    "crops": [
      {
        "crop_id": "rice",                        // Required: Crop identifier
        "name": "Rice",                           // Required: Human-readable name
        "area_per_unit": 0.25,                    // Required: Area per unit in m²
        "variety": "Koshihikari",                 // Optional: Variety/cultivar
        "revenue_per_area": 30000.0,              // Optional: Revenue per m² in ¥
        "max_revenue": 1000000.0,                 // Optional: Max revenue cap in ¥
        "groups": ["Poaceae", "grain_crops"],     // Optional: Crop groups for interaction rules
        "target_area": 1000.0                     // Optional: Optimization target area in m²
      },
      {
        "crop_id": "tomato",
        "name": "Tomato",
        "area_per_unit": 0.5,
        "variety": "Momotaro",
        "revenue_per_area": 50000.0,
        "groups": ["Solanaceae", "fruiting_vegetables"],
        "target_area": 500.0
      }
    ]
  }
  
  Crop Entity Fields:
    - crop_id (required): Stable identifier (e.g., "rice", "tomato")
    - name (required): Human-readable crop name
    - area_per_unit (required): Area occupied per unit in m²
    - variety (optional): Variety/cultivar label (e.g., "Koshihikari")
    - revenue_per_area (optional): Revenue per square meter (¥/m²)
    - max_revenue (optional): Maximum revenue constraint (¥) - represents market limits
    - groups (optional): List of group identifiers for interaction rules
    - target_area (optional): Optimization parameter - target cultivation area in m²

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
  - The algorithm uses Greedy + Local Search (Hill Climbing)
  - Target area is optional; if not specified, optimizer will determine optimal area
  - Weather file can be generated using 'agrr weather' command
  - Crop requirements are auto-generated using AI if not provided via --crop-requirement-file
  - Interaction rules allow modeling continuous cultivation impacts
            """
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        optimize_parser = subparsers.add_parser(
            "optimize", 
            help="Optimize crop allocation across multiple fields"
        )
        optimize_parser.add_argument(
            "--fields-file",
            "-ff",
            required=True,
            help='Path to fields configuration file (JSON)',
        )
        optimize_parser.add_argument(
            "--crops-file",
            "-cf",
            required=True,
            help='Path to crops configuration file (JSON)',
        )
        optimize_parser.add_argument(
            "--planning-start",
            "-s",
            required=True,
            help='Planning period start date in YYYY-MM-DD format (e.g., "2024-04-01")',
        )
        optimize_parser.add_argument(
            "--planning-end",
            "-e",
            required=True,
            help='Planning period end date in YYYY-MM-DD format (e.g., "2024-10-31")',
        )
        optimize_parser.add_argument(
            "--weather-file",
            "-w",
            required=True,
            help='Path to weather data file (JSON or CSV)',
        )
        optimize_parser.add_argument(
            "--objective",
            "-obj",
            choices=["maximize_profit", "minimize_cost"],
            default="maximize_profit",
            help="Optimization objective (default: maximize_profit)",
        )
        optimize_parser.add_argument(
            "--interaction-rules-file",
            "-irf",
            required=False,
            help='Path to interaction rules JSON file (optional, for continuous cultivation impact)',
        )
        optimize_parser.add_argument(
            "--max-time",
            "-mt",
            type=float,
            required=False,
            help="Maximum computation time in seconds (optional)",
        )
        optimize_parser.add_argument(
            "--format",
            "-fmt",
            choices=["table", "json"],
            default="table",
            help="Output format (default: table)",
        )
        optimize_parser.add_argument(
            "--enable-parallel",
            action="store_true",
            help="Enable parallel candidate generation for faster computation",
        )
        optimize_parser.add_argument(
            "--disable-local-search",
            action="store_true",
            help="Disable local search (greedy only)",
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

    def _load_fields_from_file(self, fields_file: str) -> List[str]:
        """Load field IDs from JSON file.
        
        Args:
            fields_file: Path to fields configuration file (JSON)
            
        Returns:
            List of field IDs
            
        Raises:
            ValueError: If file format is invalid
        """
        try:
            with open(fields_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'fields' not in data:
                raise ValueError("Fields file must contain 'fields' array")
            
            field_ids = []
            for field_data in data['fields']:
                if 'field_id' not in field_data:
                    raise ValueError("Each field must have 'field_id'")
                field_ids.append(field_data['field_id'])
            
            return field_ids
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in fields file: {str(e)}")
        except FileNotFoundError:
            raise ValueError(f"Fields file not found: {fields_file}")

    def _load_crops_from_file(self, crops_file: str) -> List[CropRequirementSpec]:
        """Load crop requirements from JSON file.
        
        Args:
            crops_file: Path to crops configuration file (JSON)
            
        Returns:
            List of CropRequirementSpec objects
            
        Raises:
            ValueError: If file format is invalid
        """
        try:
            with open(crops_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'crops' not in data:
                raise ValueError("Crops file must contain 'crops' array")
            
            crop_requirements = []
            for crop_data in data['crops']:
                if 'crop_id' not in crop_data:
                    raise ValueError("Each crop must have 'crop_id'")
                
                crop_req = CropRequirementSpec(
                    crop_id=crop_data['crop_id'],
                    variety=crop_data.get('variety'),
                    target_area=crop_data.get('target_area'),
                    crop_requirement_file=crop_data.get('crop_requirement_file'),
                )
                crop_requirements.append(crop_req)
            
            return crop_requirements
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in crops file: {str(e)}")
        except FileNotFoundError:
            raise ValueError(f"Crops file not found: {crops_file}")

    async def _load_interaction_rules(self, interaction_rules_file: str) -> List[InteractionRule]:
        """Load interaction rules from file.
        
        Args:
            interaction_rules_file: Path to interaction rules JSON file
            
        Returns:
            List of InteractionRule objects
        """
        if not self.interaction_rule_gateway:
            return []
        
        return await self.interaction_rule_gateway.load_from_file(interaction_rules_file)

    async def handle_optimize_command(self, args) -> None:
        """Handle the optimize command.
        
        Optimizes crop allocation across multiple fields to maximize profit or minimize cost.
        """
        # Parse planning period dates
        try:
            planning_start = self._parse_date(args.planning_start)
            planning_end = self._parse_date(args.planning_end)
        except ValueError as e:
            print(f'Error: {str(e)}')
            return

        # Load fields from file
        try:
            field_ids = self._load_fields_from_file(args.fields_file)
        except ValueError as e:
            print(f'Error loading fields: {str(e)}')
            return

        # Load crops from file
        try:
            crop_requirements = self._load_crops_from_file(args.crops_file)
        except ValueError as e:
            print(f'Error loading crops: {str(e)}')
            return

        # Load interaction rules if specified
        if getattr(args, 'interaction_rules_file', None):
            try:
                interaction_rules = await self._load_interaction_rules(args.interaction_rules_file)
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
        # Note: weather_data_file is NOT passed to DTO
        # It is configured at Gateway initialization (done at CLI startup)
        request = MultiFieldCropAllocationRequestDTO(
            field_ids=field_ids,
            crop_requirements=crop_requirements,
            planning_period_start=planning_start,
            planning_period_end=planning_end,
            optimization_objective=args.objective,
            max_computation_time=getattr(args, 'max_time', None),
        )

        # Execute use case
        try:
            enable_local_search = not getattr(args, 'disable_local_search', False)
            
            response = await self.interactor.execute(
                request,
                enable_local_search=enable_local_search,
                config=config,
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

        if not parsed_args.command:
            parser.print_help()
            return

        if parsed_args.command == "optimize":
            await self.handle_optimize_command(parsed_args)
        else:
            parser.print_help()

