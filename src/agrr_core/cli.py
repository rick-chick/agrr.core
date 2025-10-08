"""CLI application entry point."""

import asyncio
import sys
from typing import Optional

from agrr_core.framework.agrr_core_container import WeatherCliContainer
from agrr_core.adapter.gateways.crop_requirement_gateway_impl import CropRequirementGatewayImpl
from agrr_core.adapter.gateways.weather_gateway_impl import WeatherGatewayImpl
from agrr_core.adapter.presenters.crop_requirement_craft_presenter import CropRequirementCraftPresenter
from agrr_core.adapter.controllers.crop_cli_craft_controller import CropCliCraftController
from agrr_core.adapter.controllers.growth_progress_cli_controller import GrowthProgressCliController
from agrr_core.adapter.controllers.growth_period_optimize_cli_controller import GrowthPeriodOptimizeCliController
from agrr_core.framework.services.llm_client_impl import FrameworkLLMClient
from agrr_core.adapter.repositories.weather_file_repository import WeatherFileRepository
from agrr_core.framework.repositories.file_repository import FileRepository


def main() -> None:
    """Main entry point for CLI application."""
    try:
        # Create container with configuration
        config = {
            'open_meteo_base_url': 'https://archive-api.open-meteo.com/v1/archive'
        }
        container = WeatherCliContainer(config)
        
        # Get command line arguments (excluding script name)
        args = sys.argv[1:] if len(sys.argv) > 1 else None
        
        # Check subcommands
        if args and args[0] == 'predict-file':
            # Run file-based prediction CLI
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
            
            # Create crop requirement gateway with both LLM and file repository
            crop_requirement_gateway = CropRequirementGatewayImpl(
                llm_client=llm_client,
                file_repository=file_repository
            )
            
            # Setup presenter
            from agrr_core.adapter.presenters.growth_period_optimize_cli_presenter import GrowthPeriodOptimizeCliPresenter
            presenter = GrowthPeriodOptimizeCliPresenter(output_format="table")
            
            controller = GrowthPeriodOptimizeCliController(
                crop_requirement_gateway=crop_requirement_gateway,
                weather_gateway=weather_gateway,
                presenter=presenter,
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
