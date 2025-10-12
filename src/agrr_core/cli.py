"""CLI application entry point."""

import argparse
import asyncio
import sys
from typing import Optional

from agrr_core.framework.agrr_core_container import WeatherCliContainer
from agrr_core.adapter.gateways.crop_requirement_gateway_impl import CropRequirementGatewayImpl
from agrr_core.adapter.gateways.weather_gateway_impl import WeatherGatewayImpl
from agrr_core.adapter.gateways.optimization_result_gateway_impl import OptimizationResultGatewayImpl
from agrr_core.adapter.gateways.interaction_rule_gateway_impl import InteractionRuleGatewayImpl
from agrr_core.adapter.presenters.crop_requirement_craft_presenter import CropRequirementCraftPresenter
from agrr_core.adapter.controllers.crop_cli_craft_controller import CropCliCraftController
from agrr_core.adapter.controllers.growth_progress_cli_controller import GrowthProgressCliController
from agrr_core.adapter.controllers.growth_period_optimize_cli_controller import GrowthPeriodOptimizeCliController
from agrr_core.framework.services.llm_client_impl import FrameworkLLMClient
from agrr_core.adapter.repositories.weather_file_repository import WeatherFileRepository
from agrr_core.adapter.repositories.field_file_repository import FieldFileRepository
from agrr_core.framework.repositories.file_repository import FileRepository
from agrr_core.framework.repositories.inmemory_optimization_result_repository import InMemoryOptimizationResultRepository


def print_help() -> None:
    """Print main help message."""
    help_text = """
agrr - Agricultural Resource & Risk management core CLI

Usage:
  agrr <command> [options]

Available Commands:
  weather           Get historical weather data from Open-Meteo API
  forecast          Get 16-day weather forecast from tomorrow
  crop              Get crop growth requirements using AI
  progress          Calculate crop growth progress based on weather data
  optimize-period   Find optimal cultivation period to minimize costs
  predict           Predict future weather using ARIMA time series model

Examples:
  # Get historical weather data for Tokyo (last 7 days)
  agrr weather --location 35.6762,139.6503 --days 7

  # Get 16-day weather forecast
  agrr forecast --location 35.6762,139.6503

  # Get crop requirements with AI
  agrr crop --query "トマト"

  # Calculate growth progress
  agrr progress --crop rice --variety Koshihikari --start-date 2024-05-01 --weather-file weather.json

  # Find optimal planting date
  agrr optimize-period optimize --crop rice --variety Koshihikari \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \\
    --weather-file weather.json --field-config field_01.json

  # Find optimal planting date with continuous cultivation consideration
  agrr optimize-period optimize --crop tomato --variety Aiko \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \\
    --weather-file weather.json --field-config field_01.json \\
    --interaction-rules interaction_rules.json

  # Predict future weather with ARIMA model
  agrr weather --location 35.6762,139.6503 --days 90 --json > historical.json
  agrr predict --input historical.json --output predictions.json --days 30

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
         "sunshine_duration": 28800.0
       }
     ]
   }

2. Crop Requirement File (JSON):
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
  - Interaction rules allow you to model continuous cultivation impacts,
    crop rotation benefits, and field-crop compatibility.
  - See INTERACTION_RULE_USAGE.md for detailed rule types and examples.

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
        
        # Create container with configuration
        config = {
            'open_meteo_base_url': 'https://archive-api.open-meteo.com/v1/archive'
        }
        container = WeatherCliContainer(config)
        
        # Check subcommands
        if args[0] == 'predict':
            # Run ARIMA prediction CLI
            asyncio.run(container.run_prediction_cli(args))
        elif args and args[0] == 'crop':
            # Run crop requirement craft CLI (direct wiring per project rules)
            llm_client = FrameworkLLMClient()
            gateway = CropRequirementGatewayImpl(llm_client=llm_client)
            presenter = CropRequirementCraftPresenter()
            controller = CropCliCraftController(gateway=gateway, presenter=presenter)
            asyncio.run(controller.run(args[1:]))
        elif args and args[0] == 'progress':
            # Run growth progress calculation CLI
            llm_client = FrameworkLLMClient()
            crop_requirement_gateway = CropRequirementGatewayImpl(llm_client=llm_client)
            
            # Setup file-based weather repository
            file_repository = FileRepository()
            weather_file_repository = WeatherFileRepository(file_repository=file_repository)
            weather_gateway = WeatherGatewayImpl(weather_file_repository=weather_file_repository)
            
            # Setup presenter
            from agrr_core.adapter.presenters.growth_progress_cli_presenter import GrowthProgressCLIPresenter
            presenter = GrowthProgressCLIPresenter(output_format="table")
            
            controller = GrowthProgressCliController(
                crop_requirement_gateway=crop_requirement_gateway,
                weather_gateway=weather_gateway,
                presenter=presenter,
            )
            asyncio.run(controller.run(args[1:]))
        elif args and args[0] == 'optimize-period':
            # Run optimal growth period calculation CLI
            llm_client = FrameworkLLMClient()
            
            # Setup file-based repositories
            file_repository = FileRepository()
            weather_file_repository = WeatherFileRepository(file_repository=file_repository)
            weather_gateway = WeatherGatewayImpl(weather_file_repository=weather_file_repository)
            
            # Load field configuration
            # Parse args to extract field-config path
            field = None
            if '--field-config' in args or '-fc' in args:
                try:
                    fc_index = args.index('--field-config') if '--field-config' in args else args.index('-fc')
                    if fc_index + 1 < len(args):
                        field_config_path = args[fc_index + 1]
                        # Read field configuration from JSON file
                        field_file_repository = FieldFileRepository(file_repository=file_repository)
                        fields = asyncio.run(field_file_repository.read_fields_from_file(field_config_path))
                        if fields:
                            field = fields[0]  # Use first field (single field format)
                except (ValueError, IndexError) as e:
                    print(f"Error loading field configuration: {e}")
            
            # Create crop requirement gateway with both LLM and file repository
            crop_requirement_gateway = CropRequirementGatewayImpl(
                llm_client=llm_client,
                file_repository=file_repository
            )
            
            # Setup optimization result storage (in-memory)
            optimization_result_repository = InMemoryOptimizationResultRepository()
            optimization_result_gateway = OptimizationResultGatewayImpl(
                repository=optimization_result_repository
            )
            
            # Setup interaction rule gateway
            interaction_rule_gateway = InteractionRuleGatewayImpl(
                file_repository=file_repository
            )
            
            # Setup presenter
            from agrr_core.adapter.presenters.growth_period_optimize_cli_presenter import GrowthPeriodOptimizeCliPresenter
            presenter = GrowthPeriodOptimizeCliPresenter(output_format="table")
            
            controller = GrowthPeriodOptimizeCliController(
                crop_requirement_gateway=crop_requirement_gateway,
                weather_gateway=weather_gateway,
                presenter=presenter,
                field=field,
                optimization_result_gateway=optimization_result_gateway,
                interaction_rule_gateway=interaction_rule_gateway,
            )
            asyncio.run(controller.run(args[1:]))
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
