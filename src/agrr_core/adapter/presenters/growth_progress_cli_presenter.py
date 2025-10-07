"""CLI Presenter for growth progress calculation results.

This presenter formats growth progress calculation results for command-line display,
supporting both table and JSON output formats.
"""

import json
from typing import Dict, Any

from agrr_core.usecase.dto.growth_progress_calculate_response_dto import (
    GrowthProgressCalculateResponseDTO,
)
from agrr_core.usecase.ports.output.growth_progress_calculate_output_port import (
    GrowthProgressCalculateOutputPort,
)


class GrowthProgressCLIPresenter(GrowthProgressCalculateOutputPort):
    """Presenter for CLI output of growth progress calculations."""

    def __init__(self, output_format: str = "table"):
        """Initialize presenter with output format.

        Args:
            output_format: Either 'table' or 'json'
        """
        self.output_format = output_format
        self.response = None

    def present(self, response: GrowthProgressCalculateResponseDTO) -> None:
        """Present the growth progress calculation results.

        Args:
            response: Response DTO containing growth progress timeline
        """
        self.response = response

        if self.output_format == "json":
            self._present_json()
        else:
            self._present_table()

    def _present_table(self) -> None:
        """Present results in table format."""
        if not self.response:
            return

        print(f"\n=== Growth Progress for {self.response.crop_name} ===")
        if self.response.variety:
            print(f"Variety: {self.response.variety}")
        print(f"Start Date: {self.response.start_date.strftime('%Y-%m-%d')}")
        print(f"Total Records: {len(self.response.progress_records)}\n")

        # Table header
        print(
            f"{'Date':<12} {'Stage':<20} {'GDD':>10} {'Progress':>10} {'Complete':>10}"
        )
        print("-" * 65)

        # Table rows
        for record in self.response.progress_records:
            date_str = record.date.strftime("%Y-%m-%d")
            gdd_str = f"{record.cumulative_gdd:.1f}"
            progress_str = f"{record.growth_percentage:.1f}%"
            complete_str = "Yes" if record.is_complete else "No"

            print(
                f"{date_str:<12} {record.stage_name:<20} {gdd_str:>10} {progress_str:>10} {complete_str:>10}"
            )

        # Summary
        if self.response.progress_records:
            final_record = self.response.progress_records[-1]
            print(f"\nFinal Progress: {final_record.growth_percentage:.1f}%")
            print(
                f"Total GDD Accumulated: {final_record.cumulative_gdd:.1f} / {final_record.total_required_gdd:.1f}"
            )

    def _present_json(self) -> None:
        """Present results in JSON format."""
        if not self.response:
            return

        output = self.response.to_dict()
        print(json.dumps(output, indent=2, ensure_ascii=False))

    def get_output(self) -> Dict[str, Any]:
        """Get the formatted output as a dictionary.

        Returns:
            Dictionary containing the formatted response
        """
        if not self.response:
            return {}
        return self.response.to_dict()

