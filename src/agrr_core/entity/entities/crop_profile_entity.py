"""Aggregate binding a Crop to its per-stage requirements.

This aggregate holds the set of `StageRequirement` entries for a given `Crop`.
It ensures ordering and lookup by stage name, enabling clean use in interactors
without exposing repository/service concerns in the domain layer.
"""

from dataclasses import dataclass
from typing import List, Dict

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement


@dataclass(frozen=True)
class CropProfile:
    """Associates a crop with an ordered list of stage requirements.

    Invariants
    - `stage_requirements` must have unique `GrowthStage.order` and be sorted.
    - Stage names should be unique within the list for stable lookup.
    """

    crop: Crop
    stage_requirements: List[StageRequirement]

    def by_stage_name(self) -> Dict[str, StageRequirement]:
        """Return a mapping from stage name to its requirement."""
        return {sr.stage.name: sr for sr in self.stage_requirements}



