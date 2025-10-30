"""DTOs for fertilizer use cases."""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FertilizerListRequestDTO:
    """Request DTO for fertilizer list search."""
    language: str
    limit: int = 5
    area_m2: Optional[float] = None

@dataclass
class FertilizerListResponseDTO:
    """Response DTO for fertilizer list search."""
    fertilizers: List[str]

@dataclass
class FertilizerDetailRequestDTO:
    """Request DTO for fertilizer detail search."""
    fertilizer_name: str

@dataclass
class FertilizerDetailResponseDTO:
    """Response DTO for fertilizer detail search."""
    name: str
    npk: str
    manufacturer: Optional[str] = None
    product_type: Optional[str] = None
    additional_info: Optional[str] = None
    description: str = ""
    link: Optional[str] = None

