"""CLI controller for fertilizer detail use case."""

from typing import Optional
from agrr_core.usecase.interactors.fertilizer_detail_interactor import FertilizerDetailInteractor
from agrr_core.usecase.dto.fertilizer_dto import FertilizerDetailRequestDTO
from agrr_core.adapter.presenters.fertilizer_cli_presenter import FertilizerDetailCliPresenter


class FertilizerDetailCliController:
    """CLI controller for fertilizer detail information."""
    
    def __init__(self, interactor: FertilizerDetailInteractor):
        """Initialize controller.
        
        Args:
            interactor: FertilizerDetailInteractor
        """
        self.interactor = interactor
        self.presenter = FertilizerDetailCliPresenter()
    
    async def execute(self, fertilizer_name: str, json_output: bool = False) -> str:
        """Execute fertilizer detail command.
        
        Args:
            fertilizer_name: Name of the fertilizer
            json_output: Whether to output as JSON
            
        Returns:
            Formatted output string
        """
        try:
            # Create request DTO
            request = FertilizerDetailRequestDTO(fertilizer_name=fertilizer_name)
            
            # Execute interactor
            response = await self.interactor.execute(request)
            
            # Format output
            if json_output:
                return self.presenter.format_detail_json(response)
            else:
                return self.presenter.format_detail(response)
        
        except Exception as e:
            return f"Error: {str(e)}"

