"""CLI presenters for fertilizer use cases."""

import json
from typing import List

from agrr_core.usecase.dto.fertilizer_dto import FertilizerDetailResponseDTO

class FertilizerListCliPresenter:
    """Presenter for fertilizer list results in CLI format."""
    
    @staticmethod
    def format_list(fertilizers: List[str]) -> str:
        """Format fertilizer list as text output.
        
        Args:
            fertilizers: List of fertilizer names
            
        Returns:
            Formatted text output
        """
        if not fertilizers:
            return "No fertilizers found."
        
        output = f"Found {len(fertilizers)} fertilizer(s):\n\n"
        for i, fertilizer in enumerate(fertilizers, 1):
            output += f"{i}. {fertilizer}\n"
        
        return output
    
    @staticmethod
    def format_list_json(fertilizers: List[str]) -> str:
        """Format fertilizer list as JSON output.
        
        Args:
            fertilizers: List of fertilizer names
            
        Returns:
            JSON formatted output
        """
        data = {
            "fertilizers": fertilizers,
            "count": len(fertilizers)
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

class FertilizerDetailCliPresenter:
    """Presenter for fertilizer detail results in CLI format."""
    
    @staticmethod
    def format_detail(response: FertilizerDetailResponseDTO) -> str:
        """Format fertilizer detail as text output.
        
        Args:
            response: FertilizerDetailResponseDTO
            
        Returns:
            Formatted text output
        """
        output = f"Fertilizer: {response.name}\n"
        output += f"NPK Ratio: {response.npk}\n"
        
        if response.manufacturer:
            output += f"Manufacturer: {response.manufacturer}\n"
        
        if response.product_type:
            output += f"Product Type: {response.product_type}\n"
        
        if response.additional_info:
            output += f"Additional Info: {response.additional_info}\n"
        
        output += f"\nDescription:\n{response.description}\n"
        
        if response.link:
            output += f"\nReference: {response.link}\n"
        
        return output
    
    @staticmethod
    def format_detail_json(response: FertilizerDetailResponseDTO) -> str:
        """Format fertilizer detail as JSON output.
        
        Args:
            response: FertilizerDetailResponseDTO
            
        Returns:
            JSON formatted output
        """
        data = {
            "name": response.name,
            "npk": response.npk,
            "manufacturer": response.manufacturer,
            "product_type": response.product_type,
            "additional_info": response.additional_info,
            "description": response.description,
            "link": response.link
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

