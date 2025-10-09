"""Field entity.

Represents a field (圃場) with its associated daily fixed cost.
Daily fixed cost includes labor, facility management, utilities, etc.

Fields:
- field_id: Unique identifier for the field
- name: Human-readable field name
- area: Field area in square meters (m²)
- daily_fixed_cost: Daily fixed cost for this field (in JPY or currency unit per day)
- location: Optional location description or identifier
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Field:
    """Represents a field with daily fixed cost information."""

    field_id: str
    name: str
    area: float
    daily_fixed_cost: float
    location: Optional[str] = None
