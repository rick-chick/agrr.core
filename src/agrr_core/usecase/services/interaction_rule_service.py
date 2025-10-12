"""Service for applying interaction rules to crop allocations.

This service checks which interaction rules apply to a given allocation
and calculates the combined impact on revenue.
"""

from typing import List, Optional

from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.entity.entities.crop_entity import Crop


class InteractionRuleService:
    """Service for applying interaction rules."""
    
    def __init__(self, rules: List[InteractionRule]):
        """Initialize with a list of interaction rules.
        
        Args:
            rules: List of InteractionRule entities
        """
        self.rules = rules
    
    def get_continuous_cultivation_impact(
        self,
        current_crop: Crop,
        previous_crop: Optional[Crop]
    ) -> float:
        """Get the impact ratio for continuous cultivation.
        
        Checks if current crop and previous crop share any groups,
        and applies matching continuous_cultivation rules.
        
        Args:
            current_crop: Crop being planted
            previous_crop: Previously planted crop (None if no previous crop)
            
        Returns:
            Combined impact ratio (product of all applicable rules).
            Returns 1.0 if no rules apply.
            
        Examples:
            # No previous crop
            >>> service = InteractionRuleService([...])
            >>> service.get_continuous_cultivation_impact(tomato, None)
            1.0
            
            # Previous crop is different family
            >>> service.get_continuous_cultivation_impact(
            ...     current_crop=tomato,  # Solanaceae
            ...     previous_crop=soybean  # Fabaceae
            ... )
            1.0
            
            # Continuous cultivation of Solanaceae
            >>> service.get_continuous_cultivation_impact(
            ...     current_crop=eggplant,  # Solanaceae
            ...     previous_crop=tomato  # Solanaceae
            ... )
            0.7  # Assuming there's a rule with impact_ratio=0.7
        """
        # No previous crop, no impact
        if previous_crop is None:
            return 1.0
        
        # If either crop has no groups, no impact
        if not current_crop.groups or not previous_crop.groups:
            return 1.0
        
        # Find all applicable continuous_cultivation rules
        combined_impact = 1.0
        
        for prev_group in previous_crop.groups:
            for curr_group in current_crop.groups:
                for rule in self.rules:
                    # Only check continuous_cultivation rules
                    if rule.rule_type != "continuous_cultivation":
                        continue
                    
                    # Get impact for this group combination
                    impact = rule.get_impact(prev_group, curr_group)
                    
                    # If impact is not 1.0, apply it (multiply)
                    if impact != 1.0:
                        combined_impact *= impact
        
        return combined_impact
    
    def get_field_crop_impact(
        self,
        field_groups: Optional[List[str]],
        crop: Crop
    ) -> float:
        """Get the impact ratio for field-crop compatibility.
        
        Checks soil_compatibility and other field-crop matching rules.
        
        Args:
            field_groups: Groups that the field belongs to (e.g., ["acidic_soil"])
            crop: Crop being planted
            
        Returns:
            Combined impact ratio (product of all applicable rules).
            Returns 1.0 if no rules apply.
        """
        if not field_groups or not crop.groups:
            return 1.0
        
        combined_impact = 1.0
        
        for field_group in field_groups:
            for crop_group in crop.groups:
                for rule in self.rules:
                    # Check field-crop compatibility rules
                    if rule.rule_type in ["soil_compatibility", "climate_compatibility"]:
                        impact = rule.get_impact(field_group, crop_group)
                        if impact != 1.0:
                            combined_impact *= impact
        
        return combined_impact

