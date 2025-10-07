"""CLI controller for growth progress calculation (adapter layer)."""

import argparse
import asyncio
from datetime import datetime
from typing import Optional

from agrr_core.usecase.gateways.crop_requirement_gateway import CropRequirementGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.ports.input.growth_progress_calculate_input_port import (
    GrowthProgressCalculateInputPort,
)
from agrr_core.usecase.ports.output.growth_progress_calculate_output_port import (
    GrowthProgressCalculateOutputPort,
)
from agrr_core.usecase.interactors.growth_progress_calculate_interactor import (
    GrowthProgressCalculateInteractor,
)
from agrr_core.usecase.dto.growth_progress_calculate_request_dto import (
    GrowthProgressCalculateRequestDTO,
)
from agrr_core.usecase.dto.growth_progress_calculate_response_dto import (
    GrowthProgressCalculateResponseDTO,
)


class GrowthProgressCliController(GrowthProgressCalculateInputPort):
    """CLI controller implementing Input Port for growth progress calculation."""

    def __init__(
        self,
        crop_requirement_gateway: CropRequirementGateway,
        weather_gateway: WeatherGateway,
        presenter: GrowthProgressCalculateOutputPort,
    ) -> None:
        """Initialize with injected dependencies.
        
        Args:
            crop_requirement_gateway: Gateway for crop requirement operations
            weather_gateway: Gateway for weather data operations
            presenter: Presenter for output formatting
        """
        self.crop_requirement_gateway = crop_requirement_gateway
        self.weather_gateway = weather_gateway
        self.presenter = presenter
        
        # Instantiate interactor inside controller
        self.interactor = GrowthProgressCalculateInteractor(
            crop_requirement_gateway=self.crop_requirement_gateway,
            weather_gateway=self.weather_gateway,
        )

    async def execute(
        self, request: GrowthProgressCalculateRequestDTO
    ) -> GrowthProgressCalculateResponseDTO:
        """Execute the growth progress calculation use case.
        
        Implementation of Input Port interface.
        
        Args:
            request: Request DTO containing calculation parameters
            
        Returns:
            Response DTO containing growth progress data
        """
        return await self.interactor.execute(request)

    def create_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Growth Progress Calculator - Calculate daily growth progress",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        progress_parser = subparsers.add_parser(
            "progress", help="Calculate growth progress"
        )
        progress_parser.add_argument(
            "--crop",
            "-c",
            required=True,
            help='Crop name (e.g., "rice", "tomato")',
        )
        progress_parser.add_argument(
            "--variety",
            "-v",
            help='Variety/cultivar (e.g., "Koshihikari")',
        )
        progress_parser.add_argument(
            "--start-date",
            "-s",
            required=True,
            help='Growth start date in YYYY-MM-DD format (e.g., "2024-05-01")',
        )
        progress_parser.add_argument(
            "--weather-file",
            "-w",
            required=True,
            help='Path to weather data file (JSON or CSV)',
        )
        progress_parser.add_argument(
            "--format",
            "-f",
            choices=["table", "json"],
            default="table",
            help="Output format (default: table)",
        )

        return parser

    async def handle_progress_command(self, args) -> None:
        """Handle the progress calculation command."""
        # Parse start date
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            print('Error: Invalid date format. Use YYYY-MM-DD (e.g., "2024-05-01")')
            return

        # Update presenter format
        self.presenter.output_format = args.format

        # Create request DTO
        request = GrowthProgressCalculateRequestDTO(
            crop_id=args.crop,
            variety=args.variety,
            start_date=start_date,
            weather_data_file=args.weather_file,
        )

        # Execute use case
        try:
            response = await self.execute(request)
            self.presenter.present(response)
        except Exception as e:
            print(f"Error calculating growth progress: {str(e)}")
            import traceback
            traceback.print_exc()

    async def run(self, args: Optional[list] = None) -> None:
        """Run the controller with CLI arguments."""
        parser = self.create_argument_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.command:
            parser.print_help()
            return

        if parsed_args.command == "progress":
            await self.handle_progress_command(parsed_args)
        else:
            parser.print_help()

