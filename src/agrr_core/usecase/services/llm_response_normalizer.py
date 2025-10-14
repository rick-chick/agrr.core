"""LLM response normalization utilities.

This module provides utilities to normalize LLM response field names to
standardized formats. LLMs may return different field names depending on:
- Language (English/Japanese)
- Version changes
- Model variations
- Prompt variations

This normalizer provides centralized logic to handle all variations.
"""

from typing import Dict, Any, List


class LLMResponseNormalizer:
    """Normalize LLM response field names to standardized format.
    
    Design Pattern: Utility Class
    - Provides static methods for normalization
    - No state, pure functions
    - Centralized normalization logic
    """
    
    @staticmethod
    def normalize_stage_name(stage_data: Dict[str, Any]) -> str:
        """Normalize stage name from various possible field names.
        
        Supported field names (in priority order):
        1. stage_name (English, standard)
        2. ステージ名 (Japanese)
        3. period_name (alternative)
        4. stage (short form)
        5. name (generic)
        
        Args:
            stage_data: Stage data dictionary from LLM
            
        Returns:
            Normalized stage name, or "Unknown Stage" if not found
            
        Examples:
            >>> LLMResponseNormalizer.normalize_stage_name({"stage_name": "Vegetative"})
            'Vegetative'
            >>> LLMResponseNormalizer.normalize_stage_name({"ステージ名": "栄養成長期"})
            '栄養成長期'
            >>> LLMResponseNormalizer.normalize_stage_name({})
            'Unknown Stage'
        """
        return (
            stage_data.get("stage_name") or
            stage_data.get("ステージ名") or
            stage_data.get("period_name") or
            stage_data.get("stage") or
            stage_data.get("name") or
            "Unknown Stage"
        )
    
    @staticmethod
    def normalize_stage_description(stage_data: Dict[str, Any]) -> str:
        """Normalize stage description from various possible field names.
        
        Supported field names (in priority order):
        1. period_description
        2. description
        3. management_focus / 管理の重点
        4. management_transition_point / 管理転換点
        5. start_condition
        
        Args:
            stage_data: Stage data dictionary from LLM
            
        Returns:
            Normalized description, or empty string if not found
            
        Examples:
            >>> normalizer = LLMResponseNormalizer
            >>> normalizer.normalize_stage_description({"description": "Growth phase"})
            'Growth phase'
            >>> normalizer.normalize_stage_description({"管理の重点": "温度管理"})
            '温度管理'
            >>> normalizer.normalize_stage_description({})
            ''
        """
        return (
            stage_data.get("period_description") or
            stage_data.get("description") or
            stage_data.get("management_focus") or
            stage_data.get("管理の重点") or
            stage_data.get("management_transition_point") or
            stage_data.get("管理転換点") or
            stage_data.get("start_condition") or
            ""
        )
    
    @staticmethod
    def normalize_growth_stages_field(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize growth stages array field name.
        
        Supported field names (in priority order):
        1. growth_periods
        2. management_stages / 管理ステージ構成
        3. 管理ステージ
        4. growth_stages
        
        Args:
            data: Response data containing stages array
            
        Returns:
            List of stage dictionaries, or empty list if not found
            
        Examples:
            >>> data = {"growth_periods": [{"name": "Stage1"}]}
            >>> LLMResponseNormalizer.normalize_growth_stages_field(data)
            [{'name': 'Stage1'}]
        """
        return (
            data.get("growth_periods") or
            data.get("management_stages") or
            data.get("管理ステージ構成") or
            data.get("管理ステージ") or
            data.get("growth_stages") or
            []
        )
    
    @staticmethod
    def normalize_temperature_field(data: Dict[str, Any]) -> Dict[str, float]:
        """Normalize temperature data field names.
        
        Handles various temperature field name variations and nested structures.
        
        Supported structures:
        - Flat structure: {"base_temperature": 10.0, "optimal_min": 20.0, ...}
        - Nested structure: {"optimal_temperature_range": {"night": 18.0, "day": 25.0}}
        - Japanese field names: {"低温ストレス閾値": 12.0, ...}
        
        Args:
            data: Stage requirement data containing temperature info
            
        Returns:
            Normalized temperature data dictionary with standard field names
            
        Examples:
            >>> data = {
            ...     "temperature": {
            ...         "base_temperature": 10.0,
            ...         "optimal_temperature_range": {"night": 18.0, "day": 25.0}
            ...     }
            ... }
            >>> result = LLMResponseNormalizer.normalize_temperature_field(data)
            >>> result["base_temperature"]
            10.0
            >>> result["optimal_min"]
            18.0
        """
        temp_data = data.get("temperature", {})
        
        # Handle nested optimal temperature range
        temp_range = temp_data.get("optimal_temperature_range", {})
        
        return {
            "base_temperature": temp_data.get("base_temperature", 10.0),
            "optimal_min": (
                temp_range.get("night") or 
                temp_data.get("optimal_min", 20.0)
            ),
            "optimal_max": (
                temp_range.get("day") or 
                temp_data.get("optimal_max", 26.0)
            ),
            "low_stress_threshold": (
                temp_data.get("low_temperature_stress_threshold") or 
                temp_data.get("low_stress_threshold", 12.0)
            ),
            "high_stress_threshold": (
                temp_data.get("high_temperature_stress_threshold") or 
                temp_data.get("high_stress_threshold", 32.0)
            ),
            "frost_threshold": (
                temp_data.get("frost_damage_risk_temperature") or 
                temp_data.get("frost_threshold", 0.0)
            ),
            "sterility_risk_threshold": (
                temp_data.get("high_temperature_damage_threshold") or
                temp_data.get("high_temperature_disability_threshold") or
                temp_data.get("high_temperature_disability_risk_temperature") or
                temp_data.get("sterility_risk_threshold", 35.0)
            ),
        }
    
    @staticmethod
    def normalize_sunshine_field(data: Dict[str, Any]) -> Dict[str, float]:
        """Normalize sunshine data field names.
        
        Supported field names:
        - sunlight_requirements / sunshine / light_requirements
        - minimum_sunlight_hours / minimum_sunshine_hours
        - target_sunlight_hours / target_sunshine_hours
        
        Args:
            data: Stage requirement data containing sunshine info
            
        Returns:
            Normalized sunshine data dictionary
            
        Examples:
            >>> data = {"sunshine": {"minimum_sunshine_hours": 3.0}}
            >>> result = LLMResponseNormalizer.normalize_sunshine_field(data)
            >>> result["minimum_sunshine_hours"]
            3.0
        """
        sun_data = (
            data.get("sunlight_requirements") or 
            data.get("light_requirements") or 
            data.get("sunshine") or
            {}
        )
        
        return {
            "minimum_sunshine_hours": (
                sun_data.get("minimum_sunlight_hours") or
                sun_data.get("minimum_sunshine_hours", 3.0)
            ),
            "target_sunshine_hours": (
                sun_data.get("target_sunlight_hours") or
                sun_data.get("target_sunshine_hours", 6.0)
            ),
        }
    
    @staticmethod
    def normalize_thermal_field(data: Dict[str, Any]) -> Dict[str, float]:
        """Normalize thermal requirement data field names.
        
        Supported field names:
        - accumulated_temperature
        - growing_degree_days
        - gdd_requirements
        - thermal
        
        Args:
            data: Stage requirement data containing thermal info
            
        Returns:
            Normalized thermal data dictionary
            
        Examples:
            >>> data = {"thermal": {"required_gdd": 400.0}}
            >>> result = LLMResponseNormalizer.normalize_thermal_field(data)
            >>> result["required_gdd"]
            400.0
        """
        thermal_data = (
            data.get("accumulated_temperature") or 
            data.get("growing_degree_days") or
            data.get("gdd_requirements") or
            data.get("thermal") or
            {}
        )
        
        return {
            "required_gdd": thermal_data.get("required_gdd", 400.0),
        }

