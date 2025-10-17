"""CLI application entry point."""

import argparse
import asyncio
import sys
from typing import Optional

from agrr_core.framework.agrr_core_container import WeatherCliContainer
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.adapter.gateways.crop_profile_llm_gateway import CropProfileLLMGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.adapter.gateways.optimization_result_inmemory_gateway import OptimizationResultInMemoryGateway
from agrr_core.adapter.gateways.interaction_rule_file_gateway import InteractionRuleFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.presenters.crop_profile_craft_presenter import CropProfileCraftPresenter
from agrr_core.adapter.presenters.multi_field_crop_allocation_cli_presenter import MultiFieldCropAllocationCliPresenter
from agrr_core.adapter.controllers.crop_cli_craft_controller import CropCliCraftController
from agrr_core.adapter.controllers.growth_progress_cli_controller import GrowthProgressCliController
from agrr_core.adapter.controllers.growth_period_optimize_cli_controller import GrowthPeriodOptimizeCliController
from agrr_core.adapter.controllers.multi_field_crop_allocation_cli_controller import MultiFieldCropAllocationCliController
from agrr_core.framework.services.clients.llm_client import LLMClient
from agrr_core.framework.services.io.file_service import FileService
from agrr_core.adapter.services.weather_linear_interpolator import WeatherLinearInterpolator


def print_help() -> None:
    """Print main help message."""
    help_text = """
agrr - Agricultural Resource & Risk management core CLI

Usage:
  agrr <command> [options]

Available Commands:
  weather           Get historical weather data
                    - openmeteo: Global coverage, 2-3 years historical data (default)
                    - jma: Japan only, high quality, recent years
                    - noaa-ftp: US only, long-term historical data (1901-present, 2000+ recommended)
                      * 197 stations across all 50 US states
                      * Automatic year-by-year fetching for multi-year requests
                      * Free, no registration required
  forecast          Get 16-day weather forecast from tomorrow
  crop              Get crop growth profiles using AI
  progress          Calculate crop growth progress based on weather data
  optimize          Optimization tools (period, allocate)
  predict           Predict future weather using ML models (ARIMA, LightGBM)

Examples:
  # Get recent weather data (default: OpenMeteo)
  agrr weather --location 35.6762,139.6503 --days 7

  # Get Japan weather data (high quality, JMA)
  agrr weather --location 35.6762,139.6503 --days 7 --data-source jma
  
  # Get US long-term weather data (2000-2023, NOAA FTP, auto year-split)
  agrr weather --location 40.7128,-74.0060 --start-date 2000-01-01 --end-date 2023-12-31 --data-source noaa-ftp --json

  # Get 16-day weather forecast
  agrr forecast --location 35.6762,139.6503

  # Get crop profile with AI
  agrr crop --query "トマト"

  # Calculate growth progress (requires pre-generated crop profile)
  agrr crop --query "rice Koshihikari" > rice_profile.json
  agrr progress --crop-file rice_profile.json --start-date 2024-05-01 --weather-file weather.json

  # Find optimal planting date
  agrr crop --query "rice Koshihikari" > rice_profile.json
  agrr optimize period --crop-file rice_profile.json \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \\
    --weather-file weather.json --field-file field_01.json

  # Find optimal planting date with continuous cultivation consideration
  agrr crop --query "tomato Aiko" > tomato_profile.json
  agrr optimize period --crop-file tomato_profile.json \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \\
    --weather-file weather.json --field-file field_01.json \\
    --interaction-rules-file interaction_rules.json

  # Optimize crop allocation across multiple fields
  agrr optimize allocate --fields-file fields.json --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json

  # Predict future weather with ARIMA model (short-term, 30-90 days)
  agrr weather --location 35.6762,139.6503 --days 90 --json > historical.json
  agrr predict --input historical.json --output predictions.json --days 30
  
  # Predict with LightGBM model (long-term, up to 1 year, requires 90+ days data)
  agrr weather --location 35.6762,139.6503 --days 365 --data-source jma --json > historical_20y.json
  agrr predict --input historical_20y.json --output predictions.json --days 365 --model lightgbm

For detailed help on each command:
  agrr <command> --help

Input File Formats:

1. Weather Data File (JSON):
   {
     "latitude": 35.6762,
     "longitude": 139.6503,
     "elevation": 40.0,
     "timezone": "Asia/Tokyo",
     "data": [
       {
         "time": "2024-05-01",
         "temperature_2m_max": 25.5,
         "temperature_2m_min": 15.2,
         "temperature_2m_mean": 20.3,
         "precipitation_sum": 0.0,
         "sunshine_duration": 28800.0,
         "sunshine_hours": 8.0
       }
     ]
   }

2. Crop Profile File (JSON):
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
           "frost_threshold": 0.0,
           "max_temperature": 42.0         // 🆕 Required (v0.2.0+)
         },
         "thermal": {"required_gdd": 200.0}
       }
     ]
   }

3. Interaction Rules File (JSON):
   [
     {
       "rule_id": "rule_001",
       "rule_type": "continuous_cultivation",
       "source_group": "Solanaceae",
       "target_group": "Solanaceae",
       "impact_ratio": 0.7,
       "is_directional": true,
       "description": "Continuous cultivation penalty for Solanaceae"
     },
     {
       "rule_id": "rule_002",
       "rule_type": "soil_compatibility",
       "source_group": "field_001",
       "target_group": "Fabaceae",
       "impact_ratio": 1.2,
       "is_directional": true,
       "description": "Field 001 is suitable for legumes"
     }
   ]

Notes:
  - You can generate weather data using 'agrr weather' command with --json flag.
  - Crop profiles can be auto-generated using 'agrr crop' command and used directly
    as input for 'agrr progress' and 'agrr optimize period' commands.
  - The 'groups' field is essential for interaction rules (e.g., continuous cultivation).
  - Interaction rules allow you to model continuous cultivation impacts,
    crop rotation benefits, and field-crop compatibility.
  - See INTERACTION_RULE_USAGE.md for detailed rule types and examples.
  - Crop profile JSON requires 'max_temperature' - see 'agrr crop --help' for format.

"""
    print(help_text)


def main() -> None:
    """Main entry point for CLI application."""
    try:
        # Get command line arguments (excluding script name)
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        
        # Show help if no arguments or --help/-h is specified
        if not args or args[0] in ['--help', '-h', 'help']:
            print_help()
            sys.exit(0)
        
        # Extract data-source from arguments if present
        weather_data_source = 'openmeteo'  # default
        if '--data-source' in args:
            try:
                ds_index = args.index('--data-source')
                if ds_index + 1 < len(args):
                    weather_data_source = args[ds_index + 1]
            except (ValueError, IndexError):
                pass
        
        # Create container with configuration
        config = {
            'open_meteo_base_url': 'https://archive-api.open-meteo.com/v1/archive',
            'weather_data_source': weather_data_source
        }
        container = WeatherCliContainer(config)
        
        # Check subcommands
        if args[0] == 'predict':
            # Run ARIMA prediction CLI (skip 'predict' command itself)
            asyncio.run(container.run_prediction_cli(args[1:]))
        elif args and args[0] == 'crop':
            # Run crop profile craft CLI (direct wiring per project rules)
            llm_client = LLMClient()
            gateway = CropProfileLLMGateway(llm_client=llm_client)
            presenter = CropProfileCraftPresenter()
            controller = CropCliCraftController(gateway=gateway, presenter=presenter)
            asyncio.run(controller.run(args[1:]))
        elif args and args[0] == 'progress':
            # Run growth progress calculation CLI
            # Parse args to extract crop-file and weather-file paths
            file_repository = FileService()
            # Extract crop-file path
            crop_file_path = ""
            if '--crop-file' in args or '-c' in args:
                try:
                    cf_index = args.index('--crop-file') if '--crop-file' in args else args.index('-c')
                    if cf_index + 1 < len(args):
                        crop_file_path = args[cf_index + 1]
                except (ValueError, IndexError):
                    pass
            
            crop_profile_gateway = CropProfileFileGateway(
                file_repository=file_repository,
                file_path=crop_file_path
            )
            
            # Extract weather-file path
            weather_file_path = ""
            if '--weather-file' in args or '-w' in args:
                try:
                    wf_index = args.index('--weather-file') if '--weather-file' in args else args.index('-w')
                    if wf_index + 1 < len(args):
                        weather_file_path = args[wf_index + 1]
                except (ValueError, IndexError):
                    pass
            
            weather_gateway = WeatherFileGateway(file_repository=file_repository, file_path=weather_file_path)
            
            from agrr_core.adapter.presenters.growth_progress_cli_presenter import GrowthProgressCLIPresenter
            presenter = GrowthProgressCLIPresenter(output_format="table")
            
            controller = GrowthProgressCliController(
                crop_profile_gateway=crop_profile_gateway,
                weather_gateway=weather_gateway,
                presenter=presenter,
            )
            asyncio.run(controller.run(args[1:]))
        elif args and args[0] == 'optimize':
            # Unified optimize command with subcommands: period, allocate
            if len(args) < 2 or args[1] in ['--help', '-h', 'help']:
                print("""
agrr optimize - Optimization Tools

Usage:
  agrr optimize <subcommand> [options]

Available Subcommands:
  period      Find optimal cultivation period to minimize costs
  allocate    Optimize crop allocation across multiple fields

Examples:
  # Find optimal planting date
  agrr optimize period --crop-file rice.json \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \\
    --weather-file weather.json --field-file field.json

  # Optimize crop allocation
  agrr optimize allocate --fields-file fields.json --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json

For detailed help on each subcommand:
  agrr optimize period --help
  agrr optimize allocate --help
""")
                sys.exit(0)
            
            subcommand = args[1]
            
            if subcommand == 'period':
                # Run optimal growth period calculation CLI
                # Setup file-based repositories
                file_repository = FileService()
            
                # Parse args to extract crop-file path
                crop_file_path = ""
                if '--crop-file' in args or '-c' in args:
                    try:
                        cf_index = args.index('--crop-file') if '--crop-file' in args else args.index('-c')
                        if cf_index + 1 < len(args):
                            crop_file_path = args[cf_index + 1]
                    except (ValueError, IndexError):
                        pass
            
                crop_profile_gateway = CropProfileFileGateway(
                    file_repository=file_repository,
                    file_path=crop_file_path
                )
            
                # Parse args to extract weather-file path
                weather_file_path = ""
                if '--weather-file' in args or '-w' in args:
                    try:
                        wf_index = args.index('--weather-file') if '--weather-file' in args else args.index('-w')
                        if wf_index + 1 < len(args):
                            weather_file_path = args[wf_index + 1]
                    except (ValueError, IndexError):
                        pass
            
                weather_gateway = WeatherFileGateway(
                    file_repository=file_repository,
                    file_path=weather_file_path
                )
            
                # Load field configuration
                # Parse args to extract field-config path
                field = None
                if '--field-file' in args or '-f' in args:
                    try:
                        fc_index = args.index('--field-file') if '--field-file' in args else args.index('-f')
                        if fc_index + 1 < len(args):
                            field_config_path = args[fc_index + 1]
                            # Read field configuration from JSON file
                            field_file_repository = FieldFileGateway(file_repository=file_repository)
                            fields = asyncio.run(field_file_repository.read_fields_from_file(field_config_path))
                            if fields:
                                field = fields[0]  # Use first field (single field format)
                    except (ValueError, IndexError) as e:
                        print(f"Error loading field configuration: {e}")
            
            
                # Parse args to extract interaction-rules path
                # InteractionRuleFileGateway already imported at top
                interaction_rules_path = ""
                if '--interaction-rules-file' in args or '-irf' in args:
                    try:
                        ir_index = args.index('--interaction-rules-file') if '--interaction-rules-file' in args else args.index('-irf')
                        if ir_index + 1 < len(args):
                            interaction_rules_path = args[ir_index + 1]
                    except (ValueError, IndexError):
                        pass
            
                # Setup interaction rule gateway
                interaction_rule_gateway = InteractionRuleFileGateway(
                    file_repository=file_repository,
                    file_path=interaction_rules_path
                )
            
                # Setup weather interpolator
                weather_interpolator = WeatherLinearInterpolator()
            
                # Setup presenter
                from agrr_core.adapter.presenters.growth_period_optimize_cli_presenter import GrowthPeriodOptimizeCliPresenter
                presenter = GrowthPeriodOptimizeCliPresenter(output_format="table")
            
                controller = GrowthPeriodOptimizeCliController(
                    crop_profile_gateway=crop_profile_gateway,
                    weather_gateway=weather_gateway,
                    presenter=presenter,
                    field=field,
                    interaction_rule_gateway=interaction_rule_gateway,
                    weather_interpolator=weather_interpolator,
                )
                asyncio.run(controller.run(args[2:]))  # Skip 'optimize' and 'period'
            
            elif subcommand == 'allocate':
                # Run multi-field crop allocation optimization CLI
            
                # Check if help is requested
                if '--help' in args or '-h' in args:
                    # Create minimal controller just to show help
                    file_repository = FileService()
                    field_gateway = FieldFileGateway(file_repository=file_repository, file_path="")
                
                    weather_gateway = WeatherFileGateway(file_repository=file_repository, file_path="")
                
                    # Create dummy crop gateway for help
                    crop_profile_repo = CropProfileFileGateway(file_repository=file_repository, file_path="")
                    crop_profile_gateway = crop_profile_repo
                
                    # Create internal crop profile gateway for growth period optimizer
                    inmemory_crop_profile_repo = CropProfileInMemoryGateway()
                    crop_profile_gateway_internal = CropProfileInMemoryGateway()
                
                    presenter = MultiFieldCropAllocationCliPresenter(output_format="table")
                
                    controller = MultiFieldCropAllocationCliController(
                        field_gateway=field_gateway,
                        crop_gateway=crop_profile_gateway,
                        weather_gateway=weather_gateway,
                        presenter=presenter,
                        crop_profile_gateway_internal=crop_profile_gateway_internal,
                    )
                    asyncio.run(controller.run(args[2:]))  # Skip 'optimize' and 'allocate'
                    return
            
                # Setup file-based repositories
                file_repository = FileService()
            
                # Parse args to extract weather-file path
                weather_file_path = None
                if '--weather-file' in args or '-w' in args:
                    try:
                        wf_index = args.index('--weather-file') if '--weather-file' in args else args.index('-w')
                        if wf_index + 1 < len(args):
                            weather_file_path = args[wf_index + 1]
                    except (ValueError, IndexError):
                        pass
            
                if not weather_file_path:
                    print("Error: --weather-file is required for allocate command")
                    sys.exit(1)
            
                # Setup weather gateway
                weather_gateway = WeatherFileGateway(
                    file_repository=file_repository,
                    file_path=weather_file_path
                )
            
                # Parse args to extract fields-file path
                fields_file_path = None
                if '--fields-file' in args or '-fls' in args:
                    try:
                        ff_index = args.index('--fields-file') if '--fields-file' in args else args.index('-fls')
                        if ff_index + 1 < len(args):
                            fields_file_path = args[ff_index + 1]
                    except (ValueError, IndexError):
                        pass
            
                if not fields_file_path:
                    print("Error: --fields-file is required for allocate command")
                    sys.exit(1)
            
                # Setup field gateway
                field_gateway = FieldFileGateway(
                    file_repository=file_repository,
                    file_path=fields_file_path
                )
            
                # Parse args to extract crops-file path
                crops_file_path = None
                if '--crops-file' in args or '-c' in args:
                    try:
                        cf_index = args.index('--crops-file') if '--crops-file' in args else args.index('-c')
                        if cf_index + 1 < len(args):
                            crops_file_path = args[cf_index + 1]
                    except (ValueError, IndexError):
                        pass
            
                if not crops_file_path:
                    print("Error: --crops-file is required for allocate command")
                    sys.exit(1)
            
                # Setup crop gateway
                crop_profile_gateway = CropProfileFileGateway(file_repository=file_repository, file_path=crops_file_path)
            
                # Setup interaction rule gateway (optional)
                interaction_rules_path = ""
                if '--interaction-rules-file' in args or '-irf' in args:
                    try:
                        irf_index = args.index('--interaction-rules-file') if '--interaction-rules-file' in args else args.index('-irf')
                        if irf_index + 1 < len(args):
                            interaction_rules_path = args[irf_index + 1]
                    except (ValueError, IndexError):
                        pass
            
                # InteractionRuleFileGateway already imported at top
                interaction_rule_gateway = InteractionRuleFileGateway(
                    file_repository=file_repository,
                    file_path=interaction_rules_path
                )
            
                # Setup internal crop profile gateway for growth period optimizer
                inmemory_crop_profile_repo = CropProfileInMemoryGateway()
                crop_profile_gateway_internal = CropProfileInMemoryGateway()
            
                # Setup presenter
                presenter = MultiFieldCropAllocationCliPresenter(output_format="table")
            
                # Create controller
                controller = MultiFieldCropAllocationCliController(
                    field_gateway=field_gateway,
                    crop_gateway=crop_profile_gateway,
                    weather_gateway=weather_gateway,
                    presenter=presenter,
                    crop_profile_gateway_internal=crop_profile_gateway_internal,
                    interaction_rule_gateway=interaction_rule_gateway,
                )
                asyncio.run(controller.run(args[2:]))  # Skip 'optimize' and 'allocate'
            
            else:
                print(f"Error: Unknown optimize subcommand '{subcommand}'")
                print("Available: period, allocate")
                print("Run 'agrr optimize --help' for more information")
                sys.exit(1)
        else:
            # Run standard weather CLI
            asyncio.run(container.run_cli(args))
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        try:
            print(f"\n❌ Unexpected error: {e}")
        except UnicodeEncodeError:
            print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
