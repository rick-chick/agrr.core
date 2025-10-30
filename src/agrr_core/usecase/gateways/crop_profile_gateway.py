"""Gateway interface for crop profiles."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from agrr_core.entity.entities.crop_profile_entity import CropProfile

class CropProfileGateway(ABC):
    """Gateway for crop profile data access and generation.
    
    This gateway abstracts both data retrieval (from files, databases, memory, sessions)
    and profile generation (from templates, LLMs, or other sources).
    """

    @abstractmethod
    def get_all(self) -> List[CropProfile]:
        """Get all crop profiles from the configured data source.
        
        Data sources may include: files, SQL databases, in-memory storage, sessions, etc.
        The implementation determines the actual source.
        
        Returns:
            List of all CropProfile instances
        """
        pass

    @abstractmethod
    def generate(self, crop_query: str) -> CropProfile:
        """Generate a crop profile from the given query.
        
        Generation methods may include: templates, LLMs, or other generation strategies.
        The implementation determines the actual generation method.
        
        Args:
            crop_query: Query string describing the crop (e.g., "トマト", "rice Koshihikari")
            
        Returns:
            Generated CropProfile instance
        """
        pass

    # LLM-specific methods for step-by-step profile generation
    def extract_crop_variety(self, crop_query: str) -> Dict[str, Any]:
        """Extract crop name and variety from user input.
        
        Args:
            crop_query: User input containing crop and variety information
            
        Returns:
            Dict containing crop_name and variety
        """
        raise NotImplementedError("This gateway does not support LLM operations")

    def define_growth_stages(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Define growth stages for the crop variety.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing crop_info and growth_stages
        """
        raise NotImplementedError("This gateway does not support LLM operations")

    def research_stage_requirements(
        self, crop_name: str, variety: str, stage_name: str, stage_description: str
    ) -> Dict[str, Any]:
        """Research variety-specific requirements for a specific stage.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            stage_name: Name of the growth stage
            stage_description: Description of the growth stage
            
        Returns:
            Dict containing detailed requirements for the stage
        """
        raise NotImplementedError("This gateway does not support LLM operations")

    def extract_crop_economics(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop economic information (area per unit and revenue per area).
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing area_per_unit and revenue_per_area
        """
        raise NotImplementedError("This gateway does not support LLM operations")

    def extract_crop_family(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop family (科) information.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing family (科) information
        """
        raise NotImplementedError("This gateway does not support LLM operations")

