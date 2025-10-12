"""CLI Presenter for optimal growth period calculation results.

This presenter formats optimal growth period calculation results for command-line display,
supporting table output format for Phase 1 MVP.
"""

import json
from typing import Dict, Any

from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    OptimalGrowthPeriodResponseDTO,
)
from agrr_core.usecase.ports.output.growth_period_optimize_output_port import (
    GrowthPeriodOptimizeOutputPort,
)


class GrowthPeriodOptimizeCliPresenter(GrowthPeriodOptimizeOutputPort):
    """Presenter for CLI output of optimal growth period calculations."""

    def __init__(self, output_format: str = "table"):
        """Initialize presenter with output format.

        Args:
            output_format: Either 'table' or 'json' (Phase 1: table only)
        """
        self.output_format = output_format
        self.response = None

    def present(self, response: OptimalGrowthPeriodResponseDTO) -> None:
        """Present the optimal growth period calculation results.

        Args:
            response: Response DTO containing optimal period and candidate comparisons
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

        # Header
        print(f"\n=== Optimal Growth Period Analysis ===")
        print(f"Crop: {self.response.crop_name}", end="")
        if self.response.variety:
            print(f" ({self.response.variety})", end="")
        print()
        print(f"\nField Information:")
        print(f"  Field: {self.response.field.name} ({self.response.field.field_id})")
        print(f"  Area: {self.response.field.area:,.1f} m²")
        if self.response.field.location:
            print(f"  Location: {self.response.field.location}")
        print(f"  Daily Fixed Cost: ¥{self.response.field.daily_fixed_cost:,.0f}/day")
        print()

        # Optimal solution
        print("Optimal Solution:")
        print(f"  Start Date: {self.response.optimal_start_date.strftime('%Y-%m-%d')}")
        print(f"  Completion Date: {self.response.completion_date.strftime('%Y-%m-%d')}")
        print(f"  Growth Days: {self.response.growth_days} days")
        print(f"  Total Cost: ¥{self.response.total_cost:,.0f}")
        print()

        # Candidate comparison table
        print("All Candidates:")
        print(f"{'Start Date':<15} {'Completion':<15} {'Days':>6} {'Total Cost':>15} {'Status':>10}")
        print("-" * 66)

        for candidate in self.response.candidates:
            start_str = candidate.start_date.strftime("%Y-%m-%d")
            
            if candidate.completion_date:
                completion_str = candidate.completion_date.strftime("%Y-%m-%d")
                days_str = str(candidate.growth_days)
                cost_str = f"¥{candidate.total_cost:,.0f}"
            else:
                completion_str = "N/A"
                days_str = "N/A"
                cost_str = "N/A"
            
            status_str = "← OPTIMAL" if candidate.is_optimal else ""
            
            print(
                f"{start_str:<15} {completion_str:<15} {days_str:>6} {cost_str:>15} {status_str:>10}"
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

