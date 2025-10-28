"""CLI controller for fertilizer list use case."""

from typing import Optional
from agrr_core.usecase.interactors.fertilizer_list_interactor import FertilizerListInteractor
from agrr_core.usecase.dto.fertilizer_dto import FertilizerListRequestDTO
from agrr_core.adapter.presenters.fertilizer_cli_presenter import FertilizerListCliPresenter


class FertilizerListCliController:
    """CLI controller for listing fertilizers."""
    
    def __init__(self, interactor: FertilizerListInteractor):
        """Initialize controller.
        
        Args:
            interactor: FertilizerListInteractor
        """
        self.interactor = interactor
        self.presenter = FertilizerListCliPresenter()
    
    async def execute(self, language: str, limit: int = 5, area_m2: Optional[float] = None, json_output: bool = False) -> str:
        """Execute fertilizer list command.
        
        Args:
            language: Language code (e.g., "ja", "en")
            limit: Number of results (default: 5)
            area_m2: Cultivation area in square meters (optional)
            json_output: Whether to output as JSON
            
        Returns:
            Formatted output string
        """
        try:
            # Create request DTO
            request = FertilizerListRequestDTO(language=language, limit=limit, area_m2=area_m2)
            
            # Execute interactor
            response = await self.interactor.execute(request)
            
            # Format output
            if json_output:
                return self.presenter.format_list_json(response.fertilizers)
            else:
                return self.presenter.format_list(response.fertilizers)
        
        except Exception as e:
            return f"Error: {str(e)}"

