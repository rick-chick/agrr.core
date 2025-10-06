"""Growth stage entity.

Represents a crop growth stage (e.g., sowing, vegetative, flowering, maturity)
with a stable ordering key for sequencing. This entity does not embed any
thresholds; those are modeled in `StageRequirement` via profiles.

Fields
- name: Human-readable stage name (e.g., "Flowering").
- order: Integer for ordering semantics; lower means earlier.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GrowthStage:
    """Represents a crop growth stage with an ordering index.

    The `order` field is intended for total ordering within a crop’s lifecycle
    (must be unique within a crop’s stage list).
    """

    name: str
    order: int


