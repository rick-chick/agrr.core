"""Multi-field crop allocation input port.

Defines the interface for multi-field crop allocation optimization use case.
"""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.multi_field_crop_allocation_request_dto import (
    MultiFieldCropAllocationRequestDTO,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_response_dto import (
    MultiFieldCropAllocationResponseDTO,
)

class MultiFieldCropAllocationInputPort(ABC):
    """Input port for multi-field crop allocation optimization use case."""

    @abstractmethod
    def execute(
        self, request: MultiFieldCropAllocationRequestDTO
    ) -> MultiFieldCropAllocationResponseDTO:
        """Execute the multi-field crop allocation optimization use case.

        Args:
            request: Request DTO containing fields, crops, and optimization parameters

        Returns:
            Response DTO containing optimized allocation result
        """
        pass

