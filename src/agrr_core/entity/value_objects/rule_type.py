"""Rule type enumeration for interaction rules.

Defines the types of interactions between groups (crop groups, field groups, etc.)
that can affect revenue and performance.
"""

from enum import Enum


class RuleType(str, Enum):
    """Types of interaction rules.
    
    Each rule type represents a different kind of interaction context:
    
    - CONTINUOUS_CULTIVATION: Continuous cultivation damage (temporal, directed)
      Used when the same crop group is planted repeatedly in the same field.
      
    - BENEFICIAL_ROTATION: Beneficial crop rotation (temporal, directed)
      Used when a previous crop benefits a subsequent crop.
      
    - COMPANION_PLANTING: Companion planting (spatial, undirected)
      Used when crops benefit each other when planted adjacently.
      
    - ALLELOPATHY: Allelopathy - chemical inhibition (spatial, directed)
      Used when one crop inhibits another through chemical compounds.
      
    - SOIL_COMPATIBILITY: Soil type compatibility (field-crop, directed)
      Used when certain soil types are more or less suitable for crops.
      
    - CLIMATE_COMPATIBILITY: Climate compatibility (field-crop, directed)
      Used when certain climate conditions favor specific crops.
    
    Note: By inheriting from str, these enums can be easily serialized to JSON
    and compared with string values from external sources.
    """
    
    CONTINUOUS_CULTIVATION = "continuous_cultivation"
    BENEFICIAL_ROTATION = "beneficial_rotation"
    COMPANION_PLANTING = "companion_planting"
    ALLELOPATHY = "allelopathy"
    SOIL_COMPATIBILITY = "soil_compatibility"
    CLIMATE_COMPATIBILITY = "climate_compatibility"

