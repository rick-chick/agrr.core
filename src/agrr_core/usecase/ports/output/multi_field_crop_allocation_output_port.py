"""Multi-field crop allocation output port.

Defines the interface for presenting multi-field crop allocation optimization results.
"""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.multi_field_crop_allocation_response_dto import (
    MultiFieldCropAllocationResponseDTO,
)

class MultiFieldCropAllocationOutputPort(ABC):
    """Output port for multi-field crop allocation optimization use case."""

    @abstractmethod
    def present(self, response: MultiFieldCropAllocationResponseDTO) -> None:
        """Present the multi-field crop allocation optimization results.

        Args:
            response: Response DTO containing optimization result and summary
        """
        pass

