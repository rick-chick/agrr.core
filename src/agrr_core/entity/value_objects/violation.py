"""Violation value object.

Represents a constraint violation or warning condition in a crop allocation.
"""

from dataclasses import dataclass
from typing import Optional

from agrr_core.entity.value_objects.violation_type import ViolationType


@dataclass(frozen=True)
class Violation:
    """Represents a single violation in a crop allocation.
    
    Attributes:
        violation_type: Type of violation
        code: Unique code for the violation (e.g., 'FALLOW_001')
        message: Human-readable message describing the violation
        severity: 'error' or 'warning'
        impact_ratio: Impact on revenue/yield (0.0-1.0, where 1.0 = no impact)
        details: Additional context (e.g., specific dates, thresholds)
    """
    
    violation_type: ViolationType
    code: str
    message: str
    severity: str  # 'error' or 'warning'
    impact_ratio: float = 1.0
    details: Optional[str] = None
    
    def __post_init__(self):
        """Validate violation data."""
        if not self.code:
            raise ValueError("Violation code cannot be empty")
        
        if not self.message:
            raise ValueError("Violation message cannot be empty")
        
        if self.severity not in ['error', 'warning']:
            raise ValueError(f"Invalid severity: {self.severity}. Must be 'error' or 'warning'")
        
        if not 0.0 <= self.impact_ratio <= 1.0:
            raise ValueError(f"Impact ratio must be between 0.0 and 1.0, got {self.impact_ratio}")
    
    def is_error(self) -> bool:
        """Return True if this is an error-level violation."""
        return self.severity == 'error'
    
    def is_warning(self) -> bool:
        """Return True if this is a warning-level violation."""
        return self.severity == 'warning'
