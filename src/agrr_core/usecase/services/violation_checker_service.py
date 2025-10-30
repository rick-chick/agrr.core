"""Service for checking violations in crop allocations.

This service centralizes all violation detection logic and returns
standardized Violation objects for each allocation.
"""

from typing import List, Optional, TYPE_CHECKING
from datetime import timedelta

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.value_objects.violation import Violation
from agrr_core.entity.value_objects.violation_type import ViolationType
from agrr_core.usecase.services.interaction_rule_service import InteractionRuleService

if TYPE_CHECKING:
    from agrr_core.entity.entities.weather_entity import WeatherData
    from agrr_core.entity.entities.crop_profile_entity import CropProfile

class ViolationCheckerService:
    """Service for checking violations in crop allocations."""
    
    def __init__(
        self,
        interaction_rule_service: Optional[InteractionRuleService] = None
    ):
        """Initialize the violation checker.
        
        Args:
            interaction_rule_service: Service for checking interaction rules
        """
        self.interaction_rule_service = interaction_rule_service
    
    def check_violations(
        self,
        allocation: CropAllocation,
        previous_allocation: Optional[CropAllocation] = None,
        all_allocations: Optional[List[CropAllocation]] = None,
        weather_data: Optional[List["WeatherData"]] = None,
        crop_profile: Optional["CropProfile"] = None
    ) -> List[Violation]:
        """Check for violations in an allocation.
        
        Args:
            allocation: Allocation to check
            previous_allocation: Previous allocation in the same field (optional)
            all_allocations: All allocations in the solution (optional, for area check)
            weather_data: Weather data for the allocation period (optional)
            crop_profile: Crop profile with temperature requirements (optional)
            
        Returns:
            List of Violation objects found for this allocation
        """
        violations: List[Violation] = []
        
        # Check fallow period violation
        if previous_allocation and allocation.overlaps_with_fallow(previous_allocation):
            violations.append(self._create_fallow_period_violation(
                allocation, previous_allocation
            ))
        
        # Check continuous cultivation
        if self.interaction_rule_service and previous_allocation:
            impact = self.interaction_rule_service.get_continuous_cultivation_impact(
                current_crop=allocation.crop,
                previous_crop=previous_allocation.crop
            )
            if impact < 1.0:
                violations.append(self._create_continuous_cultivation_violation(
                    allocation, previous_allocation, impact
                ))
        
        # Check field-crop compatibility
        # Note: Field groups not yet implemented, this check is skipped for now
        # if self.interaction_rule_service:
        #     impact = self.interaction_rule_service.get_field_crop_impact(
        #         field_groups=allocation.field.groups,
        #         crop=allocation.crop
        #     )
        #     if impact < 1.0:
        #         violations.append(self._create_field_crop_incompatibility_violation(
        #             allocation, impact
        #         ))
        
        # Check area constraint
        if all_allocations:
            if self._exceeds_area_capacity(allocation, all_allocations):
                violations.append(self._create_area_constraint_violation(allocation))
        
        # Check temperature stress (warning display purpose)
        if weather_data and crop_profile:
            temp_violations = self._check_temperature_stress(
                allocation, weather_data, crop_profile
            )
            violations.extend(temp_violations)
        
        return violations
    
    def is_feasible(self, violations: List[Violation]) -> bool:
        """Check if violations allow the allocation to proceed.
        
        Args:
            violations: List of violations to check
            
        Returns:
            True if no error-level violations exist
        """
        return not any(v.is_error() for v in violations)
    
    def _create_fallow_period_violation(
        self,
        allocation: CropAllocation,
        previous_allocation: CropAllocation
    ) -> Violation:
        """Create a fallow period violation."""
        required_date = previous_allocation.completion_date + timedelta(
            days=allocation.field.fallow_period_days
        )
        
        return Violation(
            violation_type=ViolationType.FALLOW_PERIOD,
            code="FALLOW_001",
            message=f"Fallow period violation: next crop must start on or after {required_date.strftime('%Y-%m-%d')}",
            severity="error",
            impact_ratio=1.0,
            details=f"Previous crop: {previous_allocation.crop.name}, Fallow period: {allocation.field.fallow_period_days} days"
        )
    
    def _create_continuous_cultivation_violation(
        self,
        allocation: CropAllocation,
        previous_allocation: CropAllocation,
        impact_ratio: float
    ) -> Violation:
        """Create a continuous cultivation violation."""
        yield_reduction = (1.0 - impact_ratio) * 100
        
        return Violation(
            violation_type=ViolationType.CONTINUOUS_CULTIVATION,
            code="CONT_CULT_001",
            message=f"Continuous cultivation: {yield_reduction:.1f}% yield reduction due to repeated cultivation",
            severity="warning",
            impact_ratio=impact_ratio,
            details=f"Previous: {previous_allocation.crop.name}, Current: {allocation.crop.name}"
        )
    
    def _create_field_crop_incompatibility_violation(
        self,
        allocation: CropAllocation,
        impact_ratio: float
    ) -> Violation:
        """Create a field-crop incompatibility violation."""
        yield_reduction = (1.0 - impact_ratio) * 100
        
        return Violation(
            violation_type=ViolationType.FIELD_CROP_INCOMPATIBILITY,
            code="COMPAT_001",
            message=f"Field-crop incompatibility: {yield_reduction:.1f}% yield reduction",
            severity="warning",
            impact_ratio=impact_ratio,
            details=f"Field: {allocation.field.field_id}, Crop: {allocation.crop.name}"
        )
    
    def _create_area_constraint_violation(self, allocation: CropAllocation) -> Violation:
        """Create an area constraint violation."""
        return Violation(
            violation_type=ViolationType.AREA_CONSTRAINT,
            code="AREA_001",
            message=f"Area constraint violated: {allocation.area_used:.2f}m² exceeds field capacity {allocation.field.area:.2f}m²",
            severity="error",
            impact_ratio=1.0,
            details=f"Field: {allocation.field.field_id}"
        )
    
    def _exceeds_area_capacity(
        self,
        allocation: CropAllocation,
        all_allocations: List[CropAllocation]
    ) -> bool:
        """Check if allocation would exceed field capacity."""
        # Calculate total area used in the field
        field_area_used = sum(
            alloc.area_used for alloc in all_allocations
            if alloc.field.field_id == allocation.field.field_id
        )
        
        # Check if total exceeds capacity (with 1% tolerance for floating point errors)
        return field_area_used > allocation.field.area * 1.01
    
    def _check_temperature_stress(
        self,
        allocation: CropAllocation,
        weather_data: List["WeatherData"],
        crop_profile: "CropProfile"
    ) -> List[Violation]:
        """Check for temperature stress violations (warning display purpose).
        
        Note: This method is for warning display only, independent from cost calculation.
        Cost calculation is performed separately by YieldImpactAccumulator.
        
        Args:
            allocation: Crop allocation to check
            weather_data: List of daily weather data
            crop_profile: Crop profile with temperature requirements
            
        Returns:
            List of Violation objects for temperature stress
        """
        violations: List[Violation] = []
        
        # Check each day's weather against temperature profiles
        for weather in weather_data:
            for stage_req in crop_profile.stage_requirements:
                profile = stage_req.temperature
                stage_name = stage_req.stage.name
                
                # High temperature stress
                if profile.is_high_temp_stress(weather.temperature_2m_max):
                    violations.append(Violation(
                        violation_type=ViolationType.HIGH_TEMP_STRESS,
                        code="HIGH_TEMP_001",
                        message=f"High temperature stress on {weather.time}: {weather.temperature_2m_max:.1f}°C",
                        severity="warning",
                        impact_ratio=1.0 - profile.high_temp_daily_impact,
                        details=f"Stage: {stage_name}, Threshold: {profile.high_stress_threshold}°C"
                    ))
                
                # Low temperature stress
                if profile.is_low_temp_stress(weather.temperature_2m_mean):
                    violations.append(Violation(
                        violation_type=ViolationType.LOW_TEMP_STRESS,
                        code="LOW_TEMP_001",
                        message=f"Low temperature stress on {weather.time}: {weather.temperature_2m_mean:.1f}°C",
                        severity="warning",
                        impact_ratio=1.0 - profile.low_temp_daily_impact,
                        details=f"Stage: {stage_name}, Threshold: {profile.low_stress_threshold}°C"
                    ))
                
                # Frost risk
                if profile.is_frost_risk(weather.temperature_2m_min):
                    violations.append(Violation(
                        violation_type=ViolationType.FROST_RISK,
                        code="FROST_001",
                        message=f"Frost risk on {weather.time}: {weather.temperature_2m_min:.1f}°C",
                        severity="warning",
                        impact_ratio=1.0 - profile.frost_daily_impact,
                        details=f"Stage: {stage_name}, Threshold: {profile.frost_threshold}°C"
                    ))
                
                # Sterility risk
                if profile.is_sterility_risk(weather.temperature_2m_max):
                    violations.append(Violation(
                        violation_type=ViolationType.STERILITY_RISK,
                        code="STERILITY_001",
                        message=f"Sterility risk on {weather.time}: {weather.temperature_2m_max:.1f}°C",
                        severity="warning",
                        impact_ratio=1.0 - profile.sterility_daily_impact,
                        details=f"Stage: {stage_name}, Threshold: {profile.sterility_risk_threshold}°C"
                    ))
        
        return violations
