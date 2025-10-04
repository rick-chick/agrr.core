"""Dependency injection container for CLI application."""

import asyncio
from typing import Dict, Any

from agrr_core.adapter.repositories.open_meteo_weather_repository import OpenMeteoWeatherRepository
from agrr_core.adapter.presenters.cli_weather_presenter import CLIWeatherPresenter
from agrr_core.adapter.controllers.cli_weather_controller import CLIWeatherController
from agrr_core.usecase.interactors.fetch_weather_data_interactor import FetchWeatherDataInteractor


class CLIContainer:
    """Dependency injection container for CLI application."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize container with configuration."""
        self.config = config or {}
        self._instances = {}
    
    def get_weather_repository(self) -> OpenMeteoWeatherRepository:
        """Get weather repository instance."""
        if 'weather_repository' not in self._instances:
            base_url = self.config.get('open_meteo_base_url', 'https://archive-api.open-meteo.com/v1/archive')
            self._instances['weather_repository'] = OpenMeteoWeatherRepository(base_url=base_url)
        return self._instances['weather_repository']
    
    def get_cli_presenter(self) -> CLIWeatherPresenter:
        """Get CLI presenter instance."""
        if 'cli_presenter' not in self._instances:
            self._instances['cli_presenter'] = CLIWeatherPresenter()
        return self._instances['cli_presenter']
    
    def get_fetch_weather_interactor(self) -> FetchWeatherDataInteractor:
        """Get fetch weather interactor instance."""
        if 'fetch_weather_interactor' not in self._instances:
            weather_repository = self.get_weather_repository()
            cli_presenter = self.get_cli_presenter()
            self._instances['fetch_weather_interactor'] = FetchWeatherDataInteractor(
                weather_data_input_port=weather_repository,
                weather_presenter_output_port=cli_presenter
            )
        return self._instances['fetch_weather_interactor']
    
    def get_cli_controller(self) -> CLIWeatherController:
        """Get CLI controller instance."""
        if 'cli_controller' not in self._instances:
            fetch_interactor = self.get_fetch_weather_interactor()
            cli_presenter = self.get_cli_presenter()
            self._instances['cli_controller'] = CLIWeatherController(
                fetch_weather_interactor=fetch_interactor,
                cli_presenter=cli_presenter
            )
        return self._instances['cli_controller']
    
    async def run_cli(self, args: list = None) -> None:
        """Run CLI application with dependency injection."""
        controller = self.get_cli_controller()
        await controller.run(args)
