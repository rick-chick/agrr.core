"""Fertilizer recommendation domain entities.

All nutrient quantities are elemental and expressed in g/m2.
"""

from dataclasses import dataclass
from typing import List, Optional

from agrr_core.entity.entities.crop_entity import Crop


@dataclass(frozen=True)
class Nutrients:
    """Elemental nutrients in g/m2.

    Attributes:
        N: Nitrogen amount in g/m2
        P: Phosphorus amount in g/m2 (elemental P)
        K: Potassium amount in g/m2 (elemental K)
    """

    N: float
    P: float
    K: float


@dataclass(frozen=True)
class FertilizerApplication:
    """Represents one application group (basal or topdress).

    Attributes:
        application_type: "basal" or "topdress"
        count: Number of applications in this group (>= 1)
        schedule_hint: Optional free-text timing hint
        nutrients: Total nutrients for this group (sum across count)
        per_application: Optional per-application nutrients when count > 1
    """

    application_type: str
    count: int
    schedule_hint: Optional[str]
    nutrients: Nutrients
    per_application: Optional[Nutrients] = None


@dataclass(frozen=True)
class FertilizerPlan:
    """Structured fertilizer recommendation for a crop.

    Attributes:
        crop: Crop identity (crop_id and name)
        totals: Total nutrients required (g/m2)
        applications: List of application groups
        sources: Citations or URLs returned by LLM
        confidence: Confidence score [0.0, 1.0]
        notes: Additional notes
    """

    crop: Crop
    totals: Nutrients
    applications: List[FertilizerApplication]
    sources: List[str]
    confidence: float
    notes: Optional[str] = None


