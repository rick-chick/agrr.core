"""CLI Presenter for multi-field crop allocation optimization results.

This presenter formats multi-field crop allocation optimization results for command-line display,
supporting both table and JSON output formats.
"""

import json
from typing import Dict, Any

from agrr_core.usecase.dto.multi_field_crop_allocation_response_dto import (
    MultiFieldCropAllocationResponseDTO,
)
from agrr_core.usecase.ports.output.multi_field_crop_allocation_output_port import (
    MultiFieldCropAllocationOutputPort,
)


class MultiFieldCropAllocationCliPresenter(MultiFieldCropAllocationOutputPort):
    """Presenter for CLI output of multi-field crop allocation optimization."""

    def __init__(self, output_format: str = "table"):
        """Initialize presenter with output format.

        Args:
            output_format: Either 'table' or 'json'
        """
        self.output_format = output_format
        self.response = None

    def present(self, response: MultiFieldCropAllocationResponseDTO) -> None:
        """Present the multi-field crop allocation optimization results.

        Args:
            response: Response DTO containing optimization result and summary
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

        result = self.response.optimization_result

        # Header
        print(f"\n{'='*100}")
        print(f"Multi-Field Crop Allocation Optimization Result")
        print(f"{'='*100}")
        print(f"\nOptimization Summary:")
        print(f"  Algorithm: {result.algorithm_used}")
        print(f"  Computation Time: {result.optimization_time:.2f} seconds")
        print(f"  Optimal: {'Yes' if result.is_optimal else 'No (Heuristic)'}")
        print()

        # Financial Summary
        print(f"Financial Summary:")
        print(f"  Total Cost:    ¥{result.total_cost:,.0f}")
        print(f"  Total Revenue: ¥{result.total_revenue:,.0f}")
        print(f"  Total Profit:  ¥{result.total_profit:,.0f}")
        print(f"  Profit Rate:   {result.profit_rate * 100:.1f}%")
        print()

        # Field Summary
        print(f"Field Summary:")
        print(f"  Total Fields:      {result.total_fields}")
        print(f"  Total Allocations: {result.total_allocations}")
        print(f"  Avg Utilization:   {result.average_field_utilization:.1f}%")
        print(f"  Crop Diversity:    {result.crop_diversity}")
        print()

        # Crop Areas
        if result.crop_areas:
            print(f"Crop Areas:")
            for crop_id, area in sorted(result.crop_areas.items()):
                print(f"  {crop_id}: {area:,.1f} m²")
            print()

        # Field Schedules
        print(f"{'='*100}")
        print(f"Field Schedules:")
        print(f"{'='*100}\n")

        for schedule in result.field_schedules:
            print(f"Field: {schedule.field.name} ({schedule.field.field_id})")
            print(f"  Area: {schedule.field.area:,.1f} m² | Utilization: {schedule.utilization_rate:.1f}%")
            print(f"  Cost: ¥{schedule.total_cost:,.0f} | Revenue: ¥{schedule.total_revenue:,.0f} | Profit: ¥{schedule.total_profit:,.0f}")
            print()

            if schedule.allocations:
                print(f"  {'Crop':<20} {'Variety':<15} {'Area (m²)':>12} {'Start Date':<12} {'End Date':<12} {'Days':>6} {'Profit':>15}")
                print(f"  {'-'*96}")
                
                for alloc in sorted(schedule.allocations, key=lambda a: a.start_date):
                    crop_name = alloc.crop.name[:20]
                    variety = (alloc.crop.variety or "")[:15]
                    area_str = f"{alloc.area_used:,.1f}"
                    start_str = alloc.start_date.strftime("%Y-%m-%d")
                    end_str = alloc.completion_date.strftime("%Y-%m-%d")
                    days_str = str(alloc.growth_days)
                    profit_str = f"¥{alloc.profit:,.0f}" if alloc.profit is not None else "N/A"
                    
                    print(f"  {crop_name:<20} {variety:<15} {area_str:>12} {start_str:<12} {end_str:<12} {days_str:>6} {profit_str:>15}")
            else:
                print(f"  No allocations")
            
            print()

        print(f"{'='*100}\n")

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

