"""LLM-based gateway for fertilizer information retrieval."""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from agrr_core.entity.entities.fertilizer_entity import (
    FertilizerListRequest,
    FertilizerListResult,
    FertilizerDetailRequest,
    FertilizerDetail,
)
from agrr_core.usecase.gateways.fertilizer_gateway import FertilizerGateway
from agrr_core.adapter.interfaces.clients.llm_client_interface import LLMClientInterface

# Debug mode - set to True for debugging
DEBUG_MODE = os.getenv("AGRRCORE_DEBUG", "false").lower() == "true"

def debug_print(message: str) -> None:
    """Print debug message if debug mode is enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def calculate_required_amount_per_area(area_m2: float) -> str:
    """Calculate required fertilizer amount per square meter based on cultivation area.
    
    Args:
        area_m2: Cultivation area in square meters
        
    Returns:
        Formatted string describing the required amount
    """
    # Base requirement: 16g N per m² for base fertilizer (according to standard agricultural practices)
    # For a typical 8-8-8 fertilizer, this means about 200g fertilizer per m²
    
    base_fertilizer_per_m2 = 200  # grams per m² for base fertilizer
    base_amount = area_m2 * base_fertilizer_per_m2 / 1000  # Convert to kg
    
    # Determine scale category
    if area_m2 < 10:
        scale = "家庭園芸"
        recommended = "小容量製品（1-5kg）"
    elif area_m2 < 50:
        scale = "小規模栽培"
        recommended = "中型製品（5-20kg）"
    elif area_m2 < 500:
        scale = "中規模農場"
        recommended = "業務用大容量製品（20-40kg袋）"
    else:
        scale = "大規模農場"
        recommended = "業務用バルク製品（40kg以上）"
    
    return f"Cultivation area: {area_m2}m² ({scale}). Estimated base fertilizer needed: {base_amount:.1f}kg. Recommended: {recommended}."

def load_prompt_template(filename: str) -> str:
    """Load prompt template from prompts directory.
    
    Args:
        filename: Name of the prompt file
        
    Returns:
        Prompt template content
    """
    import sys
    
    # Check if running as PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)  # type: ignore
        prompt_file = base_path / "prompts" / filename
    else:
        # Running in normal Python environment
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent.parent
        prompt_file = project_root / "prompts" / filename
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
    
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()

class FertilizerLLMGateway(FertilizerGateway):
    """LLM-based gateway for fertilizer information retrieval.
    
    This gateway uses LLM to search for fertilizer information.
    """
    
    def __init__(self, llm_client: LLMClientInterface):
        """Initialize LLM gateway.
        
        Args:
            llm_client: LLM client for information retrieval
        """
        self.llm_client = llm_client
    
    def search_list(self, request: FertilizerListRequest) -> FertilizerListResult:
        """Search for popular fertilizers in a given language.
        
        Args:
            request: FertilizerListRequest with language, limit, and optional area
            
        Returns:
            FertilizerListResult with fertilizer names
        """
        structure = {
            "fertilizer_products": []  # List of fertilizer product names
        }
        
        # Construct query with area information if provided
        query = f"Search for {request.limit} popular commercial fertilizers (brand products) in {request.language} language. Return the fertilizer product names."
        
        instruction = """
        Search for popular commercial fertilizer products in the specified language.
        Return a JSON object with a list of specific fertilizer product names including brand names.
        Include actual commercial products sold in that market (e.g., "Osmocote", "Miracle-Gro", "花王の農業用肥料", etc.).
        Only return the product names, no other information.
        The field name should be 'fertilizer_products'.
        """
        
        # Add area-specific instructions if area is provided
        if request.area_m2 is not None:
            area_info = calculate_required_amount_per_area(request.area_m2)
            instruction += f"\n\n{area_info}\nWhen recommending fertilizers, prioritize products suitable for the specified cultivation area."
            if request.area_m2 >= 50:
                instruction += " For areas 50m² or larger, prioritize bulk/commercial products over small-sized consumer products."
        
        debug_print(f"Searching for fertilizers in {request.language} (limit: {request.limit})")
        if request.area_m2:
            debug_print(f"Area: {request.area_m2}m²")
        
        result = self.llm_client.struct(query, structure, instruction)
        debug_print(f"Search result: {result.get('data', {})}")
        
        fertilizers = result.get("data", {}).get("fertilizer_products", [])
        
        return FertilizerListResult(fertilizers=fertilizers)
    
    def search_detail(self, request: FertilizerDetailRequest) -> FertilizerDetail:
        """Search for detailed information about a specific fertilizer.
        
        Args:
            request: FertilizerDetailRequest with fertilizer name
            
        Returns:
            FertilizerDetail with NPK, description, and link
        """
        structure = {
            "name": "",
            "npk": "",  # NPK ratio like "10-10-10" or "24-8-16"
            "manufacturer": "",  # Manufacturer name
            "product_type": "",  # Product type/category
            "additional_info": "",  # Optional additional nutrients or information
            "description": "",
            "link": ""  # Optional reference URL
        }
        
        # Construct query
        query = f"Search for detailed information about commercial fertilizer product: {request.fertilizer_name}"
        
        instruction = """
        Search for detailed information about the specified commercial fertilizer product.
        
        IMPORTANT: 
        - You MUST return the NPK ratio in the npk field. Format as "N-P-K" (e.g., "24-8-16", "10-10-10", "46-0-0").
        - Return the full product name, NPK ratio in N-P-K format, manufacturer name, product type/category,
          description of the product, and reference link if available.
        - Include any additional nutrient information in additional_info field.
        - manufacturer: Company name that produces the fertilizer
        - product_type: Category like "緩効性肥料", "液体肥料", "有機肥料", "化学肥料", etc.
        DO NOT leave the npk field empty.
        """
        
        debug_print(f"Searching for fertilizer detail: {request.fertilizer_name}")
        
        result = self.llm_client.struct(query, structure, instruction)
        debug_print(f"Detail result: {result.get('data', {})}")
        
        data = result.get("data", {})
        
        return FertilizerDetail(
            name=data.get("name", data.get("product_name", request.fertilizer_name)),
            npk=data.get("npk", ""),
            manufacturer=data.get("manufacturer") or None,
            product_type=data.get("product_type") or None,
            additional_info=data.get("additional_info") or None,
            description=data.get("description", ""),
            link=data.get("link") or data.get("amazon_link") or data.get("amazon_product_link") or None
        )

