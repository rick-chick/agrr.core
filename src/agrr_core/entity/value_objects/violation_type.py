"""Violation type enumeration.

Defines the types of violations that can occur in crop allocations.
"""

from enum import Enum

class ViolationType(str, Enum):
    """Types of violations in crop allocations.
    
    Each violation type represents a different constraint violation or
    warning condition that affects crop performance or allocation feasibility.
    
    Violation Types:
    - FALLOW_PERIOD: Time overlap in the same field considering fallow period
    - CONTINUOUS_CULTIVATION: Revenue reduction due to continuous cultivation
    - FIELD_CROP_INCOMPATIBILITY: Revenue reduction due to field-crop mismatch
    - HIGH_TEMP_STRESS: High temperature stress causing yield reduction
    - LOW_TEMP_STRESS: Low temperature stress causing yield reduction
    - FROST_RISK: Frost risk causing yield reduction
    - STERILITY_RISK: Sterility risk causing yield reduction
    - AREA_CONSTRAINT: Area usage exceeding field capacity
    
    Note: By inheriting from str, these enums can be easily serialized to JSON.
    """
    
    FALLOW_PERIOD = "fallow_period"
    CONTINUOUS_CULTIVATION = "continuous_cultivation"
    FIELD_CROP_INCOMPATIBILITY = "field_crop_incompatibility"
    HIGH_TEMP_STRESS = "high_temp_stress"
    LOW_TEMP_STRESS = "low_temp_stress"
    FROST_RISK = "frost_risk"
    STERILITY_RISK = "sterility_risk"
    AREA_CONSTRAINT = "area_constraint"
