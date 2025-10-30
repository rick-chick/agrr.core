"""Batch prediction response DTO."""

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class BatchPredictionResponseDTO:
    """DTO for batch prediction response."""
    
    results: List[Dict[str, Any]]  # Results for each location
    summary: Dict[str, Any]  # Overall summary statistics
    errors: List[Dict[str, Any]]  # Any errors encountered
    processing_time: float
