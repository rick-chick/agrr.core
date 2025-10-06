"""Utilities to build JSON schemas for LLM structured outputs (adapter layer)."""

from typing import Dict, Any


def build_stage_requirement_structure() -> Dict[str, Any]:
    """Return provider-agnostic structure for stage requirement aggregate.

    Shape:
    {
      "stages": [
        {
          "name": str|null,
          "order": number|null,
          "temperature": { ... },
          "sunshine": { ... },
          "thermal": { ... }
        }
      ]
    }
    """
    return {
        "stages": [
            {
                "name": None,
                "order": None,
                "temperature": {
                    "base_temperature": None,
                    "optimal_min": None,
                    "optimal_max": None,
                    "low_stress_threshold": None,
                    "high_stress_threshold": None,
                    "frost_threshold": None,
                    "sterility_risk_threshold": None,
                },
                "sunshine": {
                    "minimum_sunshine_hours": None,
                    "target_sunshine_hours": None,
                },
                "thermal": {
                    "required_gdd": None,
                },
            }
        ]
    }


def build_stage_requirement_descriptions() -> Dict[str, Any]:
    """Return human-readable descriptions aligned with the structure.

    Each key mirrors the structure and provides semantic guidance (units, meaning).
    """
    return {
        "stages": [
            {
                "name": "Stage name (e.g., Vegetative, Flowering)",
                "order": "Ordering index; lower means earlier stage",
                "temperature": {
                    "base_temperature": "GDD base temperature in Celsius (°C)",
                    "optimal_min": "Optimal minimum of daily mean temperature (°C)",
                    "optimal_max": "Optimal maximum of daily mean temperature (°C)",
                    "low_stress_threshold": "Daily mean below this implies low-temperature stress (°C)",
                    "high_stress_threshold": "Daily mean above this implies high-temperature stress (°C)",
                    "frost_threshold": "Daily minimum at or below this implies frost risk (°C)",
                    "sterility_risk_threshold": "Daily maximum at or above this implies sterility risk (°C)",
                },
                "sunshine": {
                    "minimum_sunshine_hours": "Minimum sunshine hours per day (h)",
                    "target_sunshine_hours": "Target sunshine hours per day (h)",
                },
                "thermal": {
                    "required_gdd": "Required growing degree days to complete the stage (°C·day)",
                },
            }
        ]
    }


