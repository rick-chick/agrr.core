"""CLI presenter for allocation adjustment output."""

import json
from typing import Optional

from agrr_core.usecase.dto.allocation_adjust_response_dto import AllocationAdjustResponseDTO

class AllocationAdjustCliPresenter:
    """Presenter for allocation adjustment CLI output."""
    
    def __init__(self, output_format: str = "table"):
        """Initialize with output format.
        
        Args:
            output_format: Output format ('table' or 'json')
        """
        self.output_format = output_format
    
    def present(self, response: AllocationAdjustResponseDTO) -> None:
        """Present the allocation adjustment response.
        
        Args:
            response: Response DTO from allocation adjustment use case
        """
        if not response.success:
            self._present_error(response)
            return
        
        if self.output_format == "json":
            self._present_json(response)
        else:
            self._present_table(response)
    
    def _present_error(self, response: AllocationAdjustResponseDTO) -> None:
        """Present error message."""
        print(f"\n❌ Error: {response.message}\n")
        
        if response.rejected_moves:
            print("Rejected Moves:")
            for rejection in response.rejected_moves:
                move = rejection.get("move")
                reason = rejection.get("reason", "Unknown reason")
                print(f"  - {move.allocation_id} ({move.action.value}): {reason}")
    
    def _present_json(self, response: AllocationAdjustResponseDTO) -> None:
        """Present response in JSON format."""
        result = response.optimized_result
        
        # Build field schedules JSON
        field_schedules_json = []
        for schedule in result.field_schedules:
            allocations_json = []
            for allocation in schedule.allocations:
                allocations_json.append({
                    "allocation_id": allocation.allocation_id,
                    "crop": {
                        "crop_id": allocation.crop.crop_id,
                        "name": allocation.crop.name,
                        "variety": allocation.crop.variety,
                        "area_per_unit": allocation.crop.area_per_unit,
                        "revenue_per_area": allocation.crop.revenue_per_area,
                        "max_revenue": allocation.crop.max_revenue,
                        "groups": allocation.crop.groups,
                    },
                    "field": {
                        "field_id": allocation.field.field_id,
                        "name": allocation.field.name,
                        "area": allocation.field.area,
                        "daily_fixed_cost": allocation.field.daily_fixed_cost,
                        "location": allocation.field.location,
                        "fallow_period_days": allocation.field.fallow_period_days,
                    },
                    "start_date": allocation.start_date.isoformat(),
                    "completion_date": allocation.completion_date.isoformat(),
                    "growth_days": allocation.growth_days,
                    "area_used": allocation.area_used,
                    "total_cost": allocation.total_cost,
                    "expected_revenue": allocation.expected_revenue,
                    "profit": allocation.profit,
                    "accumulated_gdd": allocation.accumulated_gdd,
                })
            
            field_schedules_json.append({
                "field": {
                    "field_id": schedule.field.field_id,
                    "name": schedule.field.name,
                    "area": schedule.field.area,
                    "daily_fixed_cost": schedule.field.daily_fixed_cost,
                    "location": schedule.field.location,
                    "fallow_period_days": schedule.field.fallow_period_days,
                },
                "allocations": allocations_json,
                "total_area_used": schedule.total_area_used,
                "total_cost": schedule.total_cost,
                "total_revenue": schedule.total_revenue,
                "total_profit": schedule.total_profit,
                "utilization_rate": schedule.utilization_rate,
            })
        
        # Build applied and rejected moves JSON
        applied_moves_json = [
            {
                "allocation_id": move.allocation_id,
                "action": move.action.value,
                "to_field_id": move.to_field_id,
                "to_start_date": move.to_start_date.isoformat() if move.to_start_date else None,
                "to_area": move.to_area,
            }
            for move in response.applied_moves
        ]
        
        rejected_moves_json = [
            {
                "allocation_id": rejection.get("move").allocation_id,
                "action": rejection.get("move").action.value,
                "reason": rejection.get("reason", "Unknown"),
            }
            for rejection in response.rejected_moves
        ]
        
        output = {
            "success": response.success,
            "message": response.message,
            "applied_moves": applied_moves_json,
            "rejected_moves": rejected_moves_json,
            "optimization_result": {
                "optimization_id": result.optimization_id,
                "algorithm_used": result.algorithm_used,
                "optimization_time": result.optimization_time,
                "is_optimal": result.is_optimal,
                "field_schedules": field_schedules_json,
                "total_cost": result.total_cost,
                "total_revenue": result.total_revenue,
                "total_profit": result.total_profit,
                "crop_areas": result.crop_areas,
            },
        }
        
        print(json.dumps(output, indent=2, ensure_ascii=False))
    
    def _present_table(self, response: AllocationAdjustResponseDTO) -> None:
        """Present response in table format."""
        result = response.optimized_result
        
        print("\n" + "=" * 80)
        print("ALLOCATION ADJUSTMENT RESULT")
        print("=" * 80)
        
        # Print summary
        print(f"\n✓ {response.message}")
        print(f"\nOptimization ID: {result.optimization_id}")
        print(f"Algorithm: {result.algorithm_used}")
        print(f"Computation Time: {result.optimization_time:.2f}s")
        print(f"Is Optimal: {'Yes' if result.is_optimal else 'No'}")
        
        # Print applied moves
        if response.applied_moves:
            print(f"\n{'Applied Moves':<40} {'Action':<10}")
            print("-" * 80)
            for move in response.applied_moves:
                action_detail = move.action.value
                if move.action.value == "move":
                    action_detail = f"move → {move.to_field_id} (start: {move.to_start_date.strftime('%Y-%m-%d') if move.to_start_date else 'N/A'})"
                print(f"{move.allocation_id:<40} {action_detail}")
        
        # Print rejected moves
        if response.rejected_moves:
            print(f"\n{'Rejected Moves':<40} {'Reason':<40}")
            print("-" * 80)
            for rejection in response.rejected_moves:
                move = rejection.get("move")
                reason = rejection.get("reason", "Unknown")
                print(f"{move.allocation_id:<40} {reason:<40}")
        
        # Print financial summary
        print(f"\n{'Financial Summary':<30} {'Amount':<20}")
        print("-" * 80)
        print(f"{'Total Cost':<30} ¥{result.total_cost:>15,.0f}")
        print(f"{'Total Revenue':<30} ¥{result.total_revenue:>15,.0f}")
        print(f"{'Total Profit':<30} ¥{result.total_profit:>15,.0f}")
        profit_rate = (result.total_profit / result.total_cost * 100) if result.total_cost > 0 else 0
        print(f"{'Profit Rate':<30} {profit_rate:>15.1f}%")
        
        # Print field summary
        print(f"\n{'Field Summary':<20} {'Fields':<10} {'Allocations':<15} {'Avg Utilization':<20}")
        print("-" * 80)
        avg_utilization = result.average_field_utilization
        print(f"{'Total':<20} {result.total_fields:<10} {result.total_allocations:<15} {avg_utilization:>17.1f}%")
        
        # Print crop diversity
        print(f"\nCrop Diversity: {result.crop_diversity} unique crops")
        
        # Print detailed field schedules
        print(f"\n{'FIELD SCHEDULES':<80}")
        print("=" * 80)
        
        for schedule in result.field_schedules:
            print(f"\nField: {schedule.field.name} ({schedule.field.field_id})")
            print(f"  Area: {schedule.field.area:.1f}m²")
            print(f"  Daily Fixed Cost: ¥{schedule.field.daily_fixed_cost:,.0f}/day")
            print(f"  Fallow Period: {schedule.field.fallow_period_days} days")
            print(f"  Utilization: {schedule.utilization_rate:.1f}%")
            print(f"  Profit: ¥{schedule.total_profit:,.0f}\n")
            
            if schedule.allocations:
                print(f"  {'Crop':<15} {'Start Date':<12} {'End Date':<12} {'Days':<6} {'Area':<8} {'Profit':<12}")
                print("  " + "-" * 75)
                for alloc in schedule.allocations:
                    start_str = alloc.start_date.strftime("%Y-%m-%d")
                    end_str = alloc.completion_date.strftime("%Y-%m-%d")
                    crop_name = f"{alloc.crop.name[:12]}..."  if len(alloc.crop.name) > 15 else alloc.crop.name
                    print(f"  {crop_name:<15} {start_str:<12} {end_str:<12} "
                          f"{alloc.growth_days:<6} {alloc.area_used:<8.1f} ¥{alloc.profit:>10,.0f}")
            else:
                print("  No allocations")
        
        print("\n" + "=" * 80 + "\n")

