"""Fertilizer entity definitions."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class FertilizerListRequest:
    """Request for fertilizer list search.
    
    Attributes:
        language: Language code (e.g., "ja", "en")
        limit: Number of results (default: 5)
        area_m2: Cultivation area in square meters (optional, for area-specific recommendations)
    """
    language: str
    limit: int = 5
    area_m2: Optional[float] = None


@dataclass(frozen=True)
class FertilizerListResult:
    """Result of fertilizer list search.
    
    Attributes:
        fertilizers: List of fertilizer names
    """
    fertilizers: List[str]


@dataclass(frozen=True)
class FertilizerDetailRequest:
    """Request for fertilizer detail search.
    
    Attributes:
        fertilizer_name: Name of the fertilizer to search for
    """
    fertilizer_name: str


@dataclass(frozen=True)
class FertilizerDetail:
    """Detail information about a fertilizer.
    
    Attributes:
        name: Fertilizer name
        npk: NPK ratio (N-P-K)
        manufacturer: Manufacturer name
        product_type: Product type/category
        additional_info: Additional nutrients or information
        description: Description of the fertilizer
        link: URL or reference link
    """
    name: str
    npk: str
    manufacturer: Optional[str] = None
    product_type: Optional[str] = None
    additional_info: Optional[str] = None
    description: str = ""
    link: Optional[str] = None

