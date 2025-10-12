"""Interaction rule entity.

Defines rules for interactions between groups (crop groups, field groups, etc.)
and their impact on revenue.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class InteractionRule:
    """Interaction rule between groups.
    
    Represents how two groups interact and affect revenue/performance.
    
    Fields:
    - rule_id: Unique identifier for this rule
    - rule_type: Type of interaction rule
        * "continuous_cultivation": Continuous cultivation (same group repeatedly)
        * "beneficial_rotation": Beneficial crop rotation
        * "companion_planting": Companion planting (beneficial combinations)
        * "allelopathy": Allelopathy (chemical inhibition between plants)
        * "soil_compatibility": Soil type compatibility
        * Other custom values are possible
    - source_group: Source group name (e.g., "Solanaceae", "field_001", "acidic_soil")
    - target_group: Target group name (e.g., "Solanaceae", "Brassicaceae")
    - impact_ratio: Impact coefficient on revenue
        * 1.0 = No impact
        * 0.5 = 50% reduction (negative impact)
        * 1.2 = 20% increase (positive impact)
        * 0.0 = Cultivation not possible
    - is_directional: Whether the interaction is directional
        * True: Directed relationship (source → target only)
        * False: Bidirectional relationship (mutual effect)
    - description: Optional description of the rule
    
    Examples:
        # Continuous cultivation damage (Solanaceae)
        >>> InteractionRule(
        ...     rule_id="rule_001",
        ...     rule_type="continuous_cultivation",
        ...     source_group="Solanaceae",
        ...     target_group="Solanaceae",
        ...     impact_ratio=0.7,
        ...     is_directional=True,
        ...     description="Solanaceae continuous cultivation reduces revenue by 30%"
        ... )
        
        # Beneficial rotation: Fabaceae → Poaceae
        >>> InteractionRule(
        ...     rule_id="rule_002",
        ...     rule_type="beneficial_rotation",
        ...     source_group="Fabaceae",
        ...     target_group="Poaceae",
        ...     impact_ratio=1.1,
        ...     is_directional=True,
        ...     description="Legumes to grains increases revenue by 10%"
        ... )
        
        # Field × Crop group: Soil compatibility
        >>> InteractionRule(
        ...     rule_id="rule_003",
        ...     rule_type="soil_compatibility",
        ...     source_group="field_001",
        ...     target_group="Solanaceae",
        ...     impact_ratio=1.2,
        ...     is_directional=True,
        ...     description="Field 001 soil is well-suited for Solanaceae"
        ... )
        
        # Companion planting (undirected)
        >>> InteractionRule(
        ...     rule_id="rule_004",
        ...     rule_type="companion_planting",
        ...     source_group="Solanaceae",
        ...     target_group="Lamiaceae",
        ...     impact_ratio=1.15,
        ...     is_directional=False,
        ...     description="Tomato and basil companion planting increases revenue by 15%"
        ... )
    """
    
    rule_id: str
    rule_type: str
    source_group: str
    target_group: str
    impact_ratio: float
    is_directional: bool = True
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate interaction rule invariants."""
        if self.impact_ratio < 0:
            raise ValueError(f"impact_ratio must be non-negative, got {self.impact_ratio}")
        
        if not self.source_group or not self.source_group.strip():
            raise ValueError("source_group must not be empty")
        
        if not self.target_group or not self.target_group.strip():
            raise ValueError("target_group must not be empty")
        
        if not self.rule_id or not self.rule_id.strip():
            raise ValueError("rule_id must not be empty")
        
        if not self.rule_type or not self.rule_type.strip():
            raise ValueError("rule_type must not be empty")
    
    def matches(self, group_a: str, group_b: str) -> bool:
        """Check if this rule applies to the given group pair.
        
        Args:
            group_a: First group name
            group_b: Second group name
            
        Returns:
            True if this rule applies to the group pair
            
        Examples:
            >>> rule = InteractionRule(
            ...     rule_id="rule_001",
            ...     rule_type="continuous_cultivation",
            ...     source_group="Solanaceae",
            ...     target_group="Solanaceae",
            ...     impact_ratio=0.7,
            ...     is_directional=True
            ... )
            >>> rule.matches("Solanaceae", "Solanaceae")
            True
            >>> rule.matches("Solanaceae", "Fabaceae")
            False
        """
        if self.is_directional:
            # Directed: source → target order must match
            return self.source_group == group_a and self.target_group == group_b
        else:
            # Undirected: either order is acceptable
            forward_match = self.source_group == group_a and self.target_group == group_b
            backward_match = self.source_group == group_b and self.target_group == group_a
            return forward_match or backward_match
    
    def get_impact(self, group_a: str, group_b: str) -> float:
        """Get the impact ratio for the given group pair.
        
        Args:
            group_a: First group name
            group_b: Second group name
            
        Returns:
            impact_ratio if the rule applies, 1.0 otherwise
            
        Examples:
            >>> rule = InteractionRule(
            ...     rule_id="rule_001",
            ...     rule_type="continuous_cultivation",
            ...     source_group="Solanaceae",
            ...     target_group="Solanaceae",
            ...     impact_ratio=0.7,
            ...     is_directional=True
            ... )
            >>> rule.get_impact("Solanaceae", "Solanaceae")
            0.7
            >>> rule.get_impact("Solanaceae", "Fabaceae")
            1.0
        """
        if self.matches(group_a, group_b):
            return self.impact_ratio
        return 1.0
