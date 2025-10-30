"""CLI application entry point."""

import argparse
import asyncio
import sys
from typing import Optional
from agrr_core import __version__
from agrr_core.framework.logging.agrr_logger import get_logger

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
from agrr_core.adapter.controllers.task_schedule_generation_cli_controller import TaskScheduleGenerationCLIController
from agrr_core.framework.services.clients.llm_client import LLMClient
from agrr_core.framework.services.io.file_service import FileService
from agrr_core.adapter.services.weather_linear_interpolator import WeatherLinearInterpolator
from agrr_core.adapter.gateways.task_schedule_llm_gateway import TaskScheduleLLMGateway
from agrr_core.usecase.interactors.task_schedule_generation_interactor import TaskScheduleGenerationInteractor


def print_help() -> None:
    """Print main help message."""
    help_text = """
agrr - Agricultural Resource & Risk management core CLI

Usage:
  agrr <command> [options]

Global Options:
  --version, -v  Show version and exit (current: {version})

Commands:
  weather    Get historical weather data (openmeteo/jma/noaa/noaa-ftp/nasa-power)
  forecast   Get 16-day weather forecast
  crop       Create crop profile (LLM)
  progress   Calculate crop growth progress
  optimize   Optimization tools (period, allocate, adjust)
  predict    Predict future weather (ARIMA / LightGBM)
  schedule   Generate task schedule (LLM)
  fertilize  Fertilizer information search (LLM)
  daemon     Daemon process (start/stop/status/restart)

Data sources (weather):
  - openmeteo (default, global, 2-3y history)
  - jma (Japan, high quality, recent years)
  - noaa (US+India stations, hourly→daily, 2000+)
  - noaa-ftp (US long-term 1901+, auto year-split)
  - nasa-power (global grid 1984+, coarse)

Prediction models:
  - ARIMA: short-term 7-90 days, min 30 days history, outputs temperature only
  - LightGBM: 90-365 days, min 90 days (recommended 365+ / multi-year),
      always outputs temperature, temperature_max, temperature_min regardless of --metrics
      Note: Leap day 02-29 requires at least one historical sample for that month-day

Input format (JSON):
   {
     "latitude": 35.6762,
     "longitude": 139.6503,
     "elevation": 40.0,
     "timezone": "Asia/Tokyo",
    "data": [ { "time": "YYYY-MM-DD", "temperature_2m_max": 25.5,
                 "temperature_2m_min": 15.2, "temperature_2m_mean": 20.3 } ]
  }

Output examples:
  ARIMA:
    { "predictions": [ { "date": "2024-11-01", "temperature": 18.5,
        "temperature_confidence_lower": 16.2, "temperature_confidence_upper": 20.8 } ],
      "model_type": "ARIMA", "prediction_days": 30 }

  LightGBM:
    { "predictions": [ { "date": "2024-11-01", "temperature": 18.5,
        "temperature_max": 22.0, "temperature_min": 15.0,
        "temperature_confidence_lower": 16.2, "temperature_confidence_upper": 20.8,
        "temperature_max_confidence_lower": 19.0, "temperature_max_confidence_upper": 25.0,
        "temperature_min_confidence_lower": 12.0, "temperature_min_confidence_upper": 18.0 } ],
      "model_type": "LightGBM", "prediction_days": 30,
      "metrics": ["temperature", "temperature_max", "temperature_min"] }

Quick examples:
  # Historical weather (Open-Meteo)
  agrr weather --location 35.6762,139.6503 --days 7 --json > weather.json

  # ARIMA (short-term)
  agrr predict --input weather.json --output predictions.json --days 30

  # LightGBM (mid-long term, 3 metrics auto)
  agrr predict --input weather.json --output predictions.json --days 365 --model lightgbm

  # Generate candidate suggestions
  agrr optimize candidates --allocation allocation.json --fields-file fields.json \
    --crops-file crops.json --target-crop tomato --weather-file weather.json \
    --planning-start 2024-04-01 --planning-end 2024-10-31 --output candidates.txt

  # List popular fertilizers in Japanese
  agrr fertilize list --language ja
  agrr fertilize list --language ja --area 100

Docker:
  docker compose exec web /app/lib/core/agrr predict \
    --input tmp/debug/adjust_weather_complete.json \
    --output /app/tmp/debug/prediction.json \
    --days 7 --model lightgbm
  Note: Use container paths for --input/--output.

Daemon:
  Purpose: 4.8x faster startup. All commands also work without daemon.
  Commands: agrr daemon start | status | stop | restart
  Tip: If output file is not created, try 'agrr daemon restart'.

Notifications & Logging:
  - Default: notifications OFF (email/slack disabled)
  - Config file: agrr_config.yaml (logging.level, notifications.*)
  - Env overrides: AGRR_LOG_LEVEL, AGRR_EMAIL_ENABLED, AGRR_SLACK_ENABLED, ...
  - Logs: /tmp/agrr.log (main), /tmp/agrr_daemon.log (daemon)

Troubleshooting:
  1) No output file
     - Restart daemon: agrr daemon restart
     - Check path/permissions (Docker uses /app/...)
  2) LightGBM failure
     - Ensure ≥90 days (recommended 365+). Leap day 02-29 needs historical sample.
     - For ~700 days, split or ensure leap-day history.
  3) --metrics behavior
     - LightGBM always outputs 3 metrics; --metrics is ignored for LightGBM output set.

For detailed help:
  agrr <command> --help

===============================================================================
Detailed reference (kept for completeness)
===============================================================================

Examples:
  # Get recent weather data (default: OpenMeteo)
  agrr weather --location 35.6762,139.6503 --days 7

  # Get Japan weather data (high quality, JMA)
  agrr weather --location 35.6762,139.6503 --days 7 --data-source jma
  
  # Get India weather data (2000-2024, NOAA ISD, 49 agricultural stations)
  agrr weather --location 28.5844,77.2031 --start-date 2023-01-01 --end-date 2023-12-31 --data-source noaa --json

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
  agrr optimize period --crop-file rice_profile.json \
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \
    --weather-file weather.json --field-file field_01.json

  # Find optimal planting date with continuous cultivation consideration
  agrr crop --query "tomato Aiko" > tomato_profile.json
  agrr optimize period --crop-file tomato_profile.json \
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \
    --weather-file weather.json --field-file field_01.json \
    --interaction-rules-file interaction_rules.json

  # Optimize crop allocation across multiple fields
  agrr optimize allocate --fields-file fields.json --crops-file crops.json \
    --planning-start 2024-04-01 --planning-end 2024-10-31 \
    --weather-file weather.json --format json > allocation_result.json

  # Adjust existing allocation (manual correction)
  # Note: Requires JSON output from 'agrr optimize allocate --format json'
  agrr optimize adjust --current-allocation allocation_result.json \
    --moves moves.json --weather-file weather.json \
    --fields-file fields.json --crops-file crops.json \
    --planning-start 2024-04-01 --planning-end 2024-10-31

  # Generate candidate suggestions for crop allocation optimization
  agrr optimize candidates --allocation allocation_result.json \
    --fields-file fields.json --crops-file crops.json \
    --target-crop tomato --planning-start 2024-04-01 --planning-end 2024-10-31 \
    --weather-file weather.json --output candidates.txt

  # Predict future weather with ARIMA model (short-term, 30-90 days)
  agrr weather --location 35.6762,139.6503 --days 90 --json > historical.json
  agrr predict --input historical.json --output predictions.json --days 30
  
  # Predict with LightGBM model (long-term, up to 1 year, requires 90+ days data)
  agrr weather --location 35.6762,139.6503 --days 365 --data-source jma --json > historical_20y.json
  agrr predict --input historical_20y.json --output predictions.json --days 365 --model lightgbm

  # Start daemon for faster execution (4.8x speed improvement)
  agrr daemon start
  agrr daemon status
  agrr daemon stop

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

4. Moves File (JSON) - for 'agrr optimize adjust':
  {
    "moves": [
      {
        "allocation_id": "alloc_001",      // ID from current allocation
        "action": "move",                  // "move", "remove", or "add"
        "to_field_id": "field_2",          // Target field ID
        "to_start_date": "2024-05-15",     // New start date (YYYY-MM-DD)
        "to_area": 12.0                    // Optional: area in m²
      },
      {
        "allocation_id": "alloc_002",
        "action": "remove"                 // Remove allocation
      },
      {
        "action": "add",                   // Add new crop allocation (no allocation_id needed)
        "crop_id": "tomato",               // Crop ID from crops.json
        "variety": "Momotaro",             // Optional: variety name
        "to_field_id": "field_1",          // Target field ID
        "to_start_date": "2024-06-01",     // Start date (YYYY-MM-DD)
        "to_area": 15.0                    // Required for add: area in m²
      }
    ]
  }

  Actions:
    - "move": Move existing allocation to different field/date/area
      * Requires: allocation_id
    - "remove": Remove allocation from schedule
      * Requires: allocation_id
    - "add": Add new crop allocation
      * Note: allocation_id is not needed (omit it or leave empty)

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
    # Avoid str.format on JSON braces; replace only the version token safely
    # Help is intentional stdout
    print(help_text.replace("{version}", __version__))


def main() -> None:
    """Main entry point for CLI application."""
    execute_cli_direct(sys.argv[1:] if len(sys.argv) > 1 else [])


def execute_cli_direct(args) -> None:
    """Execute CLI directly (called from main or daemon)."""
    try:
        # Get command line arguments
        
        # Show help if no arguments or --help/-h is specified
        if not args or args[0] in ['--help', '-h', 'help']:
            print_help()
            sys.exit(0)

        # Global version flag and subcommand
        logger = get_logger()
        if args[0] in ['--version', '-v', 'version']:
            # Version is intentional stdout
            print(f"agrr core version {__version__}")
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
            # Run prediction CLI (skip 'predict' command itself) - now synchronous
            container.run_prediction_cli(args[1:])
        elif args and args[0] == 'crop':
            # Run crop profile craft CLI (direct wiring per project rules)
            llm_client = LLMClient()
            gateway = CropProfileLLMGateway(llm_client=llm_client)
            presenter = CropProfileCraftPresenter()
            controller = CropCliCraftController(gateway=gateway, presenter=presenter)
            
            # Use proper event loop management to avoid httpx cleanup issues
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(controller.run(args[1:]))
            except RuntimeError:
                # Fallback to asyncio.run if event loop management fails
                asyncio.run(controller.run(args[1:]))
        elif args and args[0] == 'schedule':
            # Task schedule generation command
            parser = argparse.ArgumentParser(
                description="Generate task schedule for agricultural tasks using AI",
                formatter_class=argparse.RawDescriptionHelpFormatter,
                epilog="""
Examples:
  # Generate task schedule for tomato cultivation
  agrr schedule --crop-name "トマト" --variety "アイコ" \\
    --stage-requirements examples/schedule/stage_requirements_tomato.json \\
    --agricultural-tasks examples/schedule/agricultural_tasks_tomato.json \\
    --output tomato_schedule.json

  # Generate schedule without saving to file (display on console)
  agrr schedule --crop-name "トマト" --variety "アイコ" \\
    --stage-requirements stage_requirements.json \\
    --agricultural-tasks agricultural_tasks.json

Input File Formats:

1. Stage Requirements File (JSON):
   [
     {
       "stage": {"name": "育苗期", "order": 1},
       "temperature": {
         "base_temperature": 10.0,
         "optimal_min": 18.0,
         "optimal_max": 30.0,
         "low_stress_threshold": 10.0,
         "high_stress_threshold": 32.0,
         "frost_threshold": 0.0,
         "max_temperature": 35.0
       },
       "thermal": {"required_gdd": 200.0},
       "sunshine": {
         "minimum_sunshine_hours": 6.0,
         "target_sunshine_hours": 8.0
       }
     }
   ]

2. Agricultural Tasks File (JSON):
   [
     {
       "task_id": "soil_preparation",
       "name": "土壌準備",
       "description": "畑の土壌を耕し、肥料を混ぜ込む作業",
       "time_per_sqm": 0.1,
       "weather_dependency": "low",
       "required_tools": ["トラクター", "耕運機"],
       "skill_level": "beginner"
     }
   ]

Output Format (JSON):
   {
     "task_schedules": [
       {
         "task_id": "soil_preparation",
         "stage_order": 1,
         "gdd_trigger": 0.0,
         "gdd_tolerance": 0.0,
         "priority": 1,
         "precipitation_max": 5.0,
         "wind_speed_max": 10.0,
         "temperature_min": 5.0,
         "temperature_max": 35.0,
         "description": "土壌準備作業のスケジュール"
       }
     ],
     "total_duration_days": 45.2,
     "weather_dependencies": ["precipitation", "wind_speed", "temperature"]
   }

Sample Files:
  - examples/schedule/stage_requirements_tomato.json
  - examples/schedule/agricultural_tasks_tomato.json

Note: This command uses AI (LLM) to generate task schedules based on crop
      requirements and available agricultural tasks. The output provides
      GDD-based scheduling with weather condition constraints.
                """
            )
            parser.add_argument("--crop-name", "-c", required=True, help="Name of the crop (e.g., 'トマト', 'rice')")
            parser.add_argument("--variety", "-v", required=True, help="Variety name (e.g., 'アイコ', 'Koshihikari')")
            parser.add_argument("--stage-requirements", "-sr", required=True, help="Path to stage requirements JSON file")
            parser.add_argument("--agricultural-tasks", "-at", required=True, help="Path to agricultural tasks JSON file")
            parser.add_argument("--output", "-o", help="Path to output file (optional, displays on console if not specified)")
            
            try:
                parsed_args = parser.parse_args(args[1:])
            except SystemExit:
                return
            
            # Setup LLM client and gateway
            llm_client = LLMClient()
            task_schedule_gateway = TaskScheduleLLMGateway(llm_client)
            task_schedule_interactor = TaskScheduleGenerationInteractor(task_schedule_gateway)
            controller = TaskScheduleGenerationCLIController(task_schedule_interactor)
            
            # Execute the controller
            asyncio.run(controller.generate_schedule(
                crop_name=parsed_args.crop_name,
                variety=parsed_args.variety,
                stage_requirements_file=parsed_args.stage_requirements,
                agricultural_tasks_file=parsed_args.agricultural_tasks,
                output_file=parsed_args.output
            ))
        elif args and args[0] == 'fertilize':
            # Fertilizer information search command
            from agrr_core.adapter.gateways.fertilizer_llm_gateway import FertilizerLLMGateway
            from agrr_core.adapter.controllers.fertilizer_list_cli_controller import FertilizerListCliController
            from agrr_core.adapter.controllers.fertilizer_detail_cli_controller import FertilizerDetailCliController
            from agrr_core.usecase.interactors.fertilizer_list_interactor import FertilizerListInteractor
            from agrr_core.usecase.interactors.fertilizer_detail_interactor import FertilizerDetailInteractor
            
            # Setup LLM client and gateway
            llm_client = LLMClient()
            gateway = FertilizerLLMGateway(llm_client=llm_client)
            
            # Parse subcommand
            if len(args) < 2 or args[1] in ['--help', '-h', 'help']:
                # Help to stdout
                print("""
agrr fertilize - Fertilizer information search (LLM)

Usage:
  agrr fertilize <subcommand> [options]

Available Subcommands:
  list      Search for popular fertilizers by language
  get       Get detailed fertilizer information by name
  recommend Recommend fertilizer plan (N,P,K in g/m2)

Examples:
  # List popular fertilizers in Japanese
  agrr fertilize list --language ja

  # List fertilizers suitable for specific cultivation area
  agrr fertilize list --language ja --area 100

  # List popular fertilizers in English (limit: 10)
  agrr fertilize list --language en --limit 10

  # Get detailed fertilizer information (JSON)
  agrr fertilize get --name "尿素" --json

  # Get detailed fertilizer information (text)
  agrr fertilize get --name "urea"

  # Recommend fertilizer plan for crop
  agrr crop --query "tomato" > tomato_profile.json
  agrr fertilize recommend --crop-file tomato_profile.json --json

For detailed help on each subcommand:
  agrr fertilize list --help
  agrr fertilize get --help
  agrr fertilize recommend --help
""")
                sys.exit(0)
            
            subcommand = args[1]
            
            if subcommand == 'list':
                # Check for help first
                if '--help' in args or '-h' in args:
                    print("""
agrr fertilize list - Search for popular fertilizers by language

Usage:
  agrr fertilize list --language <lang> [options]

Required:
  --language, -l    Language code (e.g., "ja", "en")

Options:
  --limit           Number of results (default: 5)
  --area, -a        Cultivation area in square meters (optional)
  --json, -j        Output in JSON format
  --help, -h        Show this help message

Examples:
  # List popular fertilizers in Japanese
  agrr fertilize list --language ja

  # List fertilizers suitable for specific cultivation area
  agrr fertilize list --language ja --area 100

  # List popular fertilizers in English (limit: 10)
  agrr fertilize list --language en --limit 10

  # Output in JSON format
  agrr fertilize list --language ja --json
""")
                    sys.exit(0)
                
                # Parse arguments for list command
                language = ""
                limit = 5
                area_m2 = None
                json_output = False
                
                if '--language' in args or '-l' in args:
                    try:
                        lang_index = args.index('--language') if '--language' in args else args.index('-l')
                        if lang_index + 1 < len(args):
                            language = args[lang_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                if not language:
                    logger.error("Error: --language is required for fertilize list command")
                    sys.exit(1)
                
                if '--limit' in args:
                    try:
                        limit_index = args.index('--limit')
                        if limit_index + 1 < len(args):
                            limit = int(args[limit_index + 1])
                    except (ValueError, IndexError):
                        pass
                
                if '--area' in args or '-a' in args:
                    try:
                        area_index = args.index('--area') if '--area' in args else args.index('-a')
                        if area_index + 1 < len(args):
                            area_m2 = float(args[area_index + 1])
                    except (ValueError, IndexError):
                        pass
                
                json_output = '--json' in args or '-j' in args
                
                interactor = FertilizerListInteractor(gateway=gateway)
                controller = FertilizerListCliController(interactor=interactor)
                output = controller.execute(language=language, limit=limit, area_m2=area_m2, json_output=json_output)
                # Output JSON/text to stdout
                print(output)
            
            elif subcommand == 'get':
                # Check for help first
                if '--help' in args or '-h' in args:
                    print("""
agrr fertilize get - Get detailed fertilizer information by name

Usage:
  agrr fertilize get --name <fertilizer_name> [options]

Required:
  --name, -n        Name of the fertilizer to search for

Options:
  --json, -j        Output in JSON format
  --help, -h        Show this help message

Examples:
  # Get detailed fertilizer information (text)
  agrr fertilize get --name "尿素"

  # Get detailed fertilizer information (JSON)
  agrr fertilize get --name "urea" --json

  # Get information about specific product
  agrr fertilize get --name "マグァンプK"
""")
                    sys.exit(0)
                
                # Parse arguments for get command
                fertilizer_name = ""
                json_output = False
                
                if '--name' in args or '-n' in args:
                    try:
                        name_index = args.index('--name') if '--name' in args else args.index('-n')
                        if name_index + 1 < len(args):
                            fertilizer_name = args[name_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                if not fertilizer_name:
                    logger.error("Error: --name is required for fertilize get command")
                    sys.exit(1)
                
                json_output = '--json' in args or '-j' in args
                
                interactor = FertilizerDetailInteractor(gateway=gateway)
                controller = FertilizerDetailCliController(interactor=interactor)
                output = controller.execute(fertilizer_name=fertilizer_name, json_output=json_output)
                print(output)
            else:
                logger.error(f"Error: Unknown fertilize subcommand '{subcommand}'")
                logger.info("Available: list, get, recommend")
                sys.exit(1)
        
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
        elif args and args[0] == 'daemon':
            # Handle daemon commands
            from agrr_core.daemon.manager import DaemonManager
            manager = DaemonManager()
            
            if len(args) < 2:
                logger.error("Usage: agrr daemon {start|stop|status|restart}")
                sys.exit(1)
            
            command = args[1]
            if command == 'start':
                manager.start()
            elif command == 'stop':
                manager.stop()
            elif command == 'status':
                manager.status()
            elif command == 'restart':
                manager.restart()
            else:
                logger.error(f"Error: Unknown daemon command '{command}'")
                logger.info("Available: start, stop, status, restart")
                sys.exit(1)
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
  adjust      Adjust existing allocation based on move instructions
  candidates  Generate candidate suggestions for crop allocation

Examples:
  # Find optimal planting date
  agrr optimize period --crop-file rice.json \\
    --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 \\
    --weather-file weather.json --field-file field.json

  # Optimize crop allocation
  agrr optimize allocate --fields-file fields.json --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json

  # Adjust existing allocation
  agrr optimize adjust --current-allocation current_allocation.json \\
    --moves moves.json --weather-file weather.json \\
    --fields-file fields.json --crops-file crops.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31

  # Generate candidate suggestions
  agrr optimize candidates --allocation current_allocation.json \\
    --fields-file fields.json --crops-file crops.json \\
    --target-crop tomato --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json --output candidates.txt

For detailed help on each subcommand:
  agrr optimize period --help
  agrr optimize allocate --help
  agrr optimize adjust --help
  agrr optimize candidates --help
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
                        logger.error(f"Error loading field configuration: {e}")
            
            
                # Parse args to extract interaction-rules path (optional)
                # InteractionRuleFileGateway already imported at top
                interaction_rules_path = ""
                if '--interaction-rules-file' in args or '-irf' in args:
                    try:
                        ir_index = args.index('--interaction-rules-file') if '--interaction-rules-file' in args else args.index('-irf')
                        if ir_index + 1 < len(args):
                            interaction_rules_path = args[ir_index + 1]
                    except (ValueError, IndexError):
                        pass
            
                # Setup interaction rule gateway only when a valid path is provided
                interaction_rule_gateway = None
                if interaction_rules_path:
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
                controller.run(args[2:])  # Skip 'optimize' and 'period'
            
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
                    controller.run(args[2:])  # Skip 'optimize' and 'allocate'
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
                    logger.error("Error: --weather-file is required for allocate command")
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
                    logger.error("Error: --fields-file is required for allocate command")
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
                    logger.error("Error: --crops-file is required for allocate command")
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
                interaction_rule_gateway = None
                if interaction_rules_path:
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
                controller.run(args[2:])  # Skip 'optimize' and 'allocate'
            
            elif subcommand == 'adjust':
                # Run allocation adjustment CLI
                
                # Check if help is requested
                if '--help' in args or '-h' in args:
                    # Create minimal controller just to show help
                    from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
                    from agrr_core.adapter.gateways.move_instruction_file_gateway import MoveInstructionFileGateway
                    from agrr_core.adapter.controllers.allocation_adjust_cli_controller import AllocationAdjustCliController
                    from agrr_core.adapter.presenters.allocation_adjust_cli_presenter import AllocationAdjustCliPresenter
                    
                    file_repository = FileService()
                    allocation_result_gateway = AllocationResultFileGateway(file_repository, "")
                    move_instruction_gateway = MoveInstructionFileGateway(file_repository, "")
                    field_gateway = FieldFileGateway(file_repository, "")
                    weather_gateway = WeatherFileGateway(file_repository=file_repository, file_path="")
                    crop_profile_gateway = CropProfileFileGateway(file_repository=file_repository, file_path="")
                    crop_profile_gateway_internal = CropProfileInMemoryGateway()
                    presenter = AllocationAdjustCliPresenter(output_format="table")
                    
                    controller = AllocationAdjustCliController(
                        allocation_result_gateway=allocation_result_gateway,
                        move_instruction_gateway=move_instruction_gateway,
                        field_gateway=field_gateway,
                        crop_gateway=crop_profile_gateway,
                        weather_gateway=weather_gateway,
                        crop_profile_gateway_internal=crop_profile_gateway_internal,
                        presenter=presenter,
                    )
                    asyncio.run(controller.run(args[2:]))  # Skip 'optimize' and 'adjust'
                    return
                
                # Setup file-based repositories
                file_repository = FileService()
                
                # Parse args to extract file paths
                current_allocation_path = ""
                if '--current-allocation' in args or '-ca' in args:
                    try:
                        ca_index = args.index('--current-allocation') if '--current-allocation' in args else args.index('-ca')
                        if ca_index + 1 < len(args):
                            current_allocation_path = args[ca_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                if not current_allocation_path:
                    logger.error("Error: --current-allocation is required for adjust command")
                    sys.exit(1)
                
                # Parse moves file path
                moves_path = ""
                if '--moves' in args or '-m' in args:
                    try:
                        m_index = args.index('--moves') if '--moves' in args else args.index('-m')
                        if m_index + 1 < len(args):
                            moves_path = args[m_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                if not moves_path:
                    logger.error("Error: --moves is required for adjust command")
                    sys.exit(1)
                
                # Parse weather file path
                weather_file_path = ""
                if '--weather-file' in args or '-w' in args:
                    try:
                        wf_index = args.index('--weather-file') if '--weather-file' in args else args.index('-w')
                        if wf_index + 1 < len(args):
                            weather_file_path = args[wf_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                if not weather_file_path:
                    logger.error("Error: --weather-file is required for adjust command")
                    sys.exit(1)
                
                # Setup gateways
                from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
                from agrr_core.adapter.gateways.move_instruction_file_gateway import MoveInstructionFileGateway
                from agrr_core.adapter.controllers.allocation_adjust_cli_controller import AllocationAdjustCliController
                from agrr_core.adapter.presenters.allocation_adjust_cli_presenter import AllocationAdjustCliPresenter
                
                allocation_result_gateway = AllocationResultFileGateway(
                    file_repository=file_repository,
                    file_path=current_allocation_path
                )
                
                move_instruction_gateway = MoveInstructionFileGateway(
                    file_repository=file_repository,
                    file_path=moves_path
                )
                
                weather_gateway = WeatherFileGateway(
                    file_repository=file_repository,
                    file_path=weather_file_path
                )
                
                # Parse optional fields and crops files
                fields_file_path = ""
                if '--fields-file' in args or '-fs' in args:
                    try:
                        ff_index = args.index('--fields-file') if '--fields-file' in args else args.index('-fs')
                        if ff_index + 1 < len(args):
                            fields_file_path = args[ff_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                field_gateway = FieldFileGateway(
                    file_repository=file_repository,
                    file_path=fields_file_path
                )
                
                crops_file_path = ""
                if '--crops-file' in args or '-cs' in args:
                    try:
                        cf_index = args.index('--crops-file') if '--crops-file' in args else args.index('-cs')
                        if cf_index + 1 < len(args):
                            crops_file_path = args[cf_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                crop_profile_gateway = CropProfileFileGateway(
                    file_repository=file_repository,
                    file_path=crops_file_path
                )
                
                # Setup interaction rule gateway (optional)
                interaction_rules_path = ""
                if '--interaction-rules-file' in args or '-irf' in args:
                    try:
                        irf_index = args.index('--interaction-rules-file') if '--interaction-rules-file' in args else args.index('-irf')
                        if irf_index + 1 < len(args):
                            interaction_rules_path = args[irf_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                interaction_rule_gateway = InteractionRuleFileGateway(
                    file_repository=file_repository,
                    file_path=interaction_rules_path
                )
                
                # Setup internal crop profile gateway
                crop_profile_gateway_internal = CropProfileInMemoryGateway()
                
                # Setup presenter
                presenter = AllocationAdjustCliPresenter(output_format="table")
                
                # Create controller
                controller = AllocationAdjustCliController(
                    allocation_result_gateway=allocation_result_gateway,
                    move_instruction_gateway=move_instruction_gateway,
                    field_gateway=field_gateway,
                    crop_gateway=crop_profile_gateway,
                    weather_gateway=weather_gateway,
                    crop_profile_gateway_internal=crop_profile_gateway_internal,
                    presenter=presenter,
                    interaction_rule_gateway=interaction_rule_gateway,
                )
                
                asyncio.run(controller.run(args[2:]))  # Skip 'optimize' and 'adjust'
            
            elif subcommand == 'candidates':
                # Run candidate suggestion CLI
                # Setup file-based repositories
                file_repository = FileService()
                
                # Parse args to extract allocation path
                allocation_path = ""
                if '--allocation' in args:
                    try:
                        alloc_index = args.index('--allocation')
                        if alloc_index + 1 < len(args):
                            allocation_path = args[alloc_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                # Setup gateways
                from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
                allocation_result_gateway = AllocationResultFileGateway(
                    file_repository=file_repository,
                    file_path=allocation_path
                )
                
                # Parse args to extract fields-file path
                fields_file_path = ""
                if '--fields-file' in args:
                    try:
                        ff_index = args.index('--fields-file')
                        if ff_index + 1 < len(args):
                            fields_file_path = args[ff_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                field_gateway = FieldFileGateway(
                    file_repository=file_repository,
                    file_path=fields_file_path
                )
                
                # Parse args to extract crops-file path
                crops_file_path = ""
                if '--crops-file' in args:
                    try:
                        cf_index = args.index('--crops-file')
                        if cf_index + 1 < len(args):
                            crops_file_path = args[cf_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                crop_gateway = CropProfileFileGateway(
                    file_repository=file_repository,
                    file_path=crops_file_path
                )
                
                # Parse args to extract weather-file path
                weather_file_path = ""
                if '--weather-file' in args:
                    try:
                        wf_index = args.index('--weather-file')
                        if wf_index + 1 < len(args):
                            weather_file_path = args[wf_index + 1]
                    except (ValueError, IndexError):
                        pass
                
                weather_gateway = WeatherFileGateway(
                    file_repository=file_repository,
                    file_path=weather_file_path
                )
                
                # Parse args to extract interaction-rules path
                interaction_rule_gateway = None
                if '--interaction-rules-file' in args:
                    try:
                        ir_index = args.index('--interaction-rules-file')
                        if ir_index + 1 < len(args):
                            interaction_rules_path = args[ir_index + 1]
                            interaction_rule_gateway = InteractionRuleFileGateway(
                                file_repository=file_repository,
                                file_path=interaction_rules_path
                            )
                    except (ValueError, IndexError):
                        pass
                
                # Setup presenter
                from agrr_core.adapter.presenters.candidate_suggestion_cli_presenter import CandidateSuggestionCliPresenter
                presenter = CandidateSuggestionCliPresenter()
                
                # Setup controller
                from agrr_core.adapter.controllers.candidate_suggestion_cli_controller import CandidateSuggestionCliController
                controller = CandidateSuggestionCliController(
                    allocation_result_gateway=allocation_result_gateway,
                    field_gateway=field_gateway,
                    crop_gateway=crop_gateway,
                    weather_gateway=weather_gateway,
                    presenter=presenter,
                    interaction_rule_gateway=interaction_rule_gateway
                )
                
                asyncio.run(controller.handle_candidates_command(controller.create_argument_parser().parse_args(args[2:])))
            
            else:
                logger.error(f"Error: Unknown optimize subcommand '{subcommand}'")
                logger.info("Available: period, allocate, adjust, candidates")
                logger.info("Run 'agrr optimize --help' for more information")
                sys.exit(1)
        else:
            # Run standard weather CLI - now synchronous
            container.run_cli(args)
        
    except KeyboardInterrupt:
        logger = get_logger()
        logger.warning("Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger = get_logger()
        import os, traceback
        if os.getenv("AGRRCORE_DEBUG", "false").lower() == "true":
            logger.error(f"[DEBUG] Exception type: {type(e).__name__}")
            logger.error(f"[DEBUG] Exception repr: {repr(e)}")
            logger.error("[DEBUG] Traceback:")
            logger.error(traceback.format_exc())
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
