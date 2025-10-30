"""Period template entity.

Represents a crop's growth period template that is independent of specific fields.
This template can be applied to any field to generate allocation candidates.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from agrr_core.entity.entities.crop_entity import Crop

if TYPE_CHECKING:
    from agrr_core.entity.entities.field_entity import Field
    from agrr_core.usecase.dto.growth_period_optimize_response_dto import CandidateResultDTO

@dataclass(frozen=True)
class PeriodTemplate:
    """Crop growth period template (Field-independent).
    
    Represents the result of sliding window GDD calculation for a specific crop
    and start date. This template is Field-independent and can be applied to
    any field to generate AllocationCandidate.
    
    Attributes:
        template_id: Unique identifier for this template
        crop: Crop entity
        start_date: Cultivation start date
        completion_date: Cultivation completion date
        growth_days: Number of days from start to completion
        accumulated_gdd: Total accumulated growing degree days
        yield_factor: Yield impact factor from temperature stress (0.0-1.0)
    """
    
    template_id: str
    crop: Crop
    start_date: datetime
    completion_date: datetime
    growth_days: int
    accumulated_gdd: float
    yield_factor: float = 1.0
    
    def __post_init__(self):
        """Validate template invariants."""
        if self.growth_days < 0:
            raise ValueError(f"growth_days must be non-negative, got {self.growth_days}")
        
        if self.accumulated_gdd < 0:
            raise ValueError(f"accumulated_gdd must be non-negative, got {self.accumulated_gdd}")
        
        if self.completion_date < self.start_date:
            raise ValueError(
                f"completion_date ({self.completion_date}) must be after or equal to start_date ({self.start_date})"
            )
        
        if not (0.0 <= self.yield_factor <= 1.0):
            raise ValueError(
                f"yield_factor must be between 0.0 and 1.0, got {self.yield_factor}"
            )
    
    def apply_to_field(
        self,
        field: 'Field',
        area_used: float
    ) -> 'AllocationCandidate':
        """Apply this template to a specific field to generate allocation candidate.
        
        Args:
            field: Target field for allocation
            area_used: Area to allocate (m²)
            
        Returns:
            AllocationCandidate with this template's timing applied to the field
        """
        # Import here to avoid circular dependency
        from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
            AllocationCandidate
        )
        
        return AllocationCandidate(
            field=field,
            crop=self.crop,
            start_date=self.start_date,
            completion_date=self.completion_date,
            growth_days=self.growth_days,
            accumulated_gdd=self.accumulated_gdd,
            area_used=area_used
        )
    
    def calculate_cost_for_field(self, field: 'Field') -> float:
        """Calculate cost for this template on a specific field.
        
        Args:
            field: Target field
            
        Returns:
            Total cost (growth_days × field.daily_fixed_cost)
        """
        return self.growth_days * field.daily_fixed_cost
    
    @staticmethod
    def from_candidate_result(
        candidate: 'CandidateResultDTO',
        crop: Crop,
        accumulated_gdd: float = 0.0
    ) -> Optional['PeriodTemplate']:
        """Create PeriodTemplate from CandidateResultDTO.
        
        Factory method to convert growth period optimization results into
        field-independent period templates.
        
        Args:
            candidate: Growth period optimization result (from GrowthPeriodOptimizeInteractor)
            crop: Crop entity
            accumulated_gdd: Total accumulated GDD (default: 0.0 if not available)
            
        Returns:
            PeriodTemplate if candidate is complete and valid, None otherwise
            
        Example:
            >>> from agrr_core.entity.entities.period_template_entity import PeriodTemplate
            >>> template = PeriodTemplate.from_candidate_result(
            ...     candidate=assessment,
            ...     crop=crop_entity,
            ...     accumulated_gdd=1500.0
            ... )
            >>> if template:
            ...     # Use template
            ...     candidate = template.apply_to_field(field, area)
        
        Note:
            Returns None for incomplete candidates (missing completion_date or growth_days).
            This allows filtering in a single step without explicit null checks.
        """
        # Validation: Skip incomplete candidates
        if candidate.completion_date is None or candidate.growth_days is None:
            return None
        
        # Generate unique template ID: {crop_id}_{start_date}
        # Example: "tomato_2025-04-01"
        template_id = f"{crop.crop_id}_{candidate.start_date.date().isoformat()}"
        
        return PeriodTemplate(
            template_id=template_id,
            crop=crop,
            start_date=candidate.start_date,
            completion_date=candidate.completion_date,
            growth_days=candidate.growth_days,
            accumulated_gdd=accumulated_gdd,
            yield_factor=candidate.yield_factor
        )

