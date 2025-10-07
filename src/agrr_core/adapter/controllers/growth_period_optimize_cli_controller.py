"""CLI controller for optimal growth period calculation (adapter layer)."""

import argparse
import asyncio
from datetime import datetime
from typing import Optional, List

from agrr_core.usecase.gateways.crop_requirement_gateway import CropRequirementGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
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


class GrowthPeriodOptimizeCliController(GrowthPeriodOptimizeInputPort):
    """CLI controller implementing Input Port for optimal growth period calculation."""

    def __init__(
        self,
        crop_requirement_gateway: CropRequirementGateway,
        weather_gateway: WeatherGateway,
        presenter: GrowthPeriodOptimizeOutputPort,
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
        self.interactor = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=self.crop_requirement_gateway,
            weather_gateway=self.weather_gateway,
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
            description="Optimal Growth Period Calculator - Find the best start date to minimize costs",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        optimize_parser = subparsers.add_parser(
            "optimize", help="Calculate optimal growth period"
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
            "--start-dates",
            "-s",
            required=True,
            help='Comma-separated candidate start dates in YYYY-MM-DD format (e.g., "2024-04-01,2024-04-15,2024-05-01")',
        )
        optimize_parser.add_argument(
            "--weather-file",
            "-w",
            required=True,
            help='Path to weather data file (JSON or CSV)',
        )
        optimize_parser.add_argument(
            "--daily-cost",
            "-d",
            type=float,
            required=True,
            help='Daily fixed cost (e.g., 5000 for ¥5,000/day)',
        )
        optimize_parser.add_argument(
            "--format",
            "-f",
            choices=["table", "json"],
            default="table",
            help="Output format (default: table)",
        )

        return parser

    def _parse_start_dates(self, dates_str: str) -> List[datetime]:
        """Parse comma-separated date strings into datetime objects.
        
        Args:
            dates_str: Comma-separated dates (e.g., "2024-04-01,2024-04-15")
            
        Returns:
            List of datetime objects
            
        Raises:
            ValueError: If date format is invalid
        """
        dates = []
        for date_str in dates_str.split(','):
            date_str = date_str.strip()
            try:
                dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
            except ValueError:
                raise ValueError(
                    f'Invalid date format: "{date_str}". Use YYYY-MM-DD (e.g., "2024-04-01")'
                )
        return dates

    async def handle_optimize_command(self, args) -> None:
        """Handle the optimize calculation command."""
        # Parse start dates
        try:
            candidate_start_dates = self._parse_start_dates(args.start_dates)
        except ValueError as e:
            print(f'Error: {str(e)}')
            return

        # Update presenter format
        self.presenter.output_format = args.format

        # Create request DTO
        request = OptimalGrowthPeriodRequestDTO(
            crop_id=args.crop,
            variety=args.variety,
            candidate_start_dates=candidate_start_dates,
            weather_data_file=args.weather_file,
            daily_fixed_cost=args.daily_cost,
        )

        # Execute use case
        try:
            response = await self.execute(request)
            self.presenter.present(response)
        except Exception as e:
            print(f"Error calculating optimal growth period: {str(e)}")
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

