"""Crop requirement craft request DTO.

Minimal request for the LLM-backed crafter. Input is a single free-form query
identifying the crop (and optionally variety), e.g., "トマト", "アイコトマト".
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class CropProfileCraftRequestDTO:
    """DTO for crafting crop stage requirement profiles via LLM."""

    crop_query: str

