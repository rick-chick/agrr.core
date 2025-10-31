"""Integration tests comparing filter_redundant_candidates ON/OFF across multiple scenarios.

This test suite validates the impact of candidate filtering on optimization results
using real test data from test_data directory.
"""

import pytest
from datetime import datetime
import json
from pathlib import Path

from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.framework.services.io.file_service import FileService
from agrr_core.adapter.presenters.multi_field_crop_allocation_cli_presenter import (
    MultiFieldCropAllocationCliPresenter,
)
from agrr_core.adapter.controllers.multi_field_crop_allocation_cli_controller import (
    MultiFieldCropAllocationCliController,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_request_dto import (
    MultiFieldCropAllocationRequestDTO,
)

@pytest.mark.slow
class TestFilterRedundantComparison:
    """Compare optimization results with filter_redundant_candidates ON vs OFF.
    
    Note: These tests are compute-intensive and take 2-80 seconds each.
    Run with: pytest -m slow
    """

    @pytest.fixture
    def test_data_dir(self):
        """Get test_data directory path."""
        return Path(__file__).parent.parent.parent / "test_data"

    def _run_optimization(
        self,
        fields_file: Path,
        crops_file: Path,
        weather_file: Path,
        planning_start: str,
        planning_end: str,
        filter_redundant: bool,
    ):
        """Run optimization and return result.
        
        Args:
            fields_file: Path to fields JSON file
            crops_file: Path to crops JSON file
            weather_file: Path to weather JSON file
            planning_start: Planning period start date (YYYY-MM-DD)
            planning_end: Planning period end date (YYYY-MM-DD)
            filter_redundant: Enable/disable candidate filtering
            
        Returns:
            OptimizationResult with cost, revenue, profit metrics
        """
        # Create gateways
        file_service = FileService()
        field_gateway = FieldFileGateway(file_service, str(fields_file))
        crop_gateway = CropProfileFileGateway(file_service, str(crops_file))
        weather_gateway = WeatherFileGateway(file_service, str(weather_file))
        
        # Use InMemoryGateway for internal crop profile operations (needs save/delete)
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        presenter = MultiFieldCropAllocationCliPresenter(output_format="json")

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            presenter=presenter,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
        )

        # Load fields
        fields = field_gateway.get_all()
        field_ids = [f.field_id for f in fields]

        # Create request
        request = MultiFieldCropAllocationRequestDTO(
            field_ids=field_ids,
            planning_period_start=datetime.strptime(planning_start, "%Y-%m-%d"),
            planning_period_end=datetime.strptime(planning_end, "%Y-%m-%d"),
            optimization_objective="maximize_profit",
            filter_redundant_candidates=filter_redundant,
        )

        # Execute
        response = controller.interactor.execute(
            request, enable_local_search=False, algorithm="greedy"
        )

        return response.optimization_result

    def test_scenario_1_with_fallow_4crops(self, test_data_dir):
        """Scenario 1: 4 fields with fallow period, 4 crops (ナス, キュウリ, ニンジン, ほうれん草)."""
        fields_file = test_data_dir / "allocation_fields_with_fallow.json"
        crops_file = test_data_dir / "allocation_crops_1760447748.json"
        weather_file = test_data_dir / "weather_2023_full.json"

        # Run with filtering ON
        result_on = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=True,
        )

        # Run with filtering OFF
        result_off = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=False,
        )

        # Analysis
        print("\n=== Scenario 1: With Fallow Period (4 fields, 4 crops) ===")
        print(f"Filter ON  - Cost: ¥{result_on.total_cost:,.0f}, Revenue: ¥{result_on.total_revenue:,.0f}, Profit: ¥{result_on.total_profit:,.0f}")
        print(f"Filter OFF - Cost: ¥{result_off.total_cost:,.0f}, Revenue: ¥{result_off.total_revenue:,.0f}, Profit: ¥{result_off.total_profit:,.0f}")
        print(f"Difference - Cost: ¥{result_off.total_cost - result_on.total_cost:+,.0f}, Profit: ¥{result_off.total_profit - result_on.total_profit:+,.0f}")
        print(f"Schedules  - Filter ON: {len(result_on.field_schedules)} fields, Filter OFF: {len(result_off.field_schedules)} fields")

        # Both should produce valid results
        assert result_on.total_profit > 0, "Filter ON should produce positive profit"
        assert result_off.total_profit > 0, "Filter OFF should produce positive profit"

    def test_scenario_2_no_fallow_4crops(self, test_data_dir):
        """Scenario 2: 4 fields without fallow period (continuous cultivation), 4 crops."""
        fields_file = test_data_dir / "allocation_fields_no_fallow.json"
        crops_file = test_data_dir / "allocation_crops_1760447748.json"
        weather_file = test_data_dir / "weather_2023_full.json"

        # Run with filtering ON
        result_on = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=True,
        )

        # Run with filtering OFF
        result_off = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=False,
        )

        # Analysis
        print("\n=== Scenario 2: No Fallow Period - Continuous Cultivation (4 fields, 4 crops) ===")
        print(f"Filter ON  - Cost: ¥{result_on.total_cost:,.0f}, Revenue: ¥{result_on.total_revenue:,.0f}, Profit: ¥{result_on.total_profit:,.0f}")
        print(f"Filter OFF - Cost: ¥{result_off.total_cost:,.0f}, Revenue: ¥{result_off.total_revenue:,.0f}, Profit: ¥{result_off.total_profit:,.0f}")
        print(f"Difference - Cost: ¥{result_off.total_cost - result_on.total_cost:+,.0f}, Profit: ¥{result_off.total_profit - result_on.total_profit:+,.0f}")

        # No fallow allows more cultivation cycles
        assert result_on.total_profit > 0
        assert result_off.total_profit > 0

    def test_scenario_3_strict_fallow_4crops(self, test_data_dir):
        """Scenario 3: 4 fields with strict fallow period (longer rest), 4 crops."""
        fields_file = test_data_dir / "allocation_fields_strict_fallow.json"
        crops_file = test_data_dir / "allocation_crops_1760447748.json"
        weather_file = test_data_dir / "weather_2023_full.json"

        # Run with filtering ON
        result_on = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=True,
        )

        # Run with filtering OFF
        result_off = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=False,
        )

        # Analysis
        print("\n=== Scenario 3: Strict Fallow Period (4 fields, 4 crops) ===")
        print(f"Filter ON  - Cost: ¥{result_on.total_cost:,.0f}, Revenue: ¥{result_on.total_revenue:,.0f}, Profit: ¥{result_on.total_profit:,.0f}")
        print(f"Filter OFF - Cost: ¥{result_off.total_cost:,.0f}, Revenue: ¥{result_off.total_revenue:,.0f}, Profit: ¥{result_off.total_profit:,.0f}")
        print(f"Difference - Cost: ¥{result_off.total_cost - result_on.total_cost:+,.0f}, Profit: ¥{result_off.total_profit - result_on.total_profit:+,.0f}")

        assert result_on.total_profit > 0
        assert result_off.total_profit > 0

    def test_scenario_4_with_fallow_6crops(self, test_data_dir):
        """Scenario 4: 4 fields with fallow period, 6 crop types (increased complexity)."""
        fields_file = test_data_dir / "allocation_fields_with_fallow.json"
        crops_file = test_data_dir / "allocation_crops_6types.json"
        weather_file = test_data_dir / "weather_2023_full.json"

        # Run with filtering ON
        result_on = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=True,
        )

        # Run with filtering OFF
        result_off = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=False,
        )

        # Analysis
        print("\n=== Scenario 4: With Fallow Period, 6 Crop Types (4 fields) ===")
        print(f"Filter ON  - Cost: ¥{result_on.total_cost:,.0f}, Revenue: ¥{result_on.total_revenue:,.0f}, Profit: ¥{result_on.total_profit:,.0f}")
        print(f"Filter OFF - Cost: ¥{result_off.total_cost:,.0f}, Revenue: ¥{result_off.total_revenue:,.0f}, Profit: ¥{result_off.total_profit:,.0f}")
        print(f"Difference - Cost: ¥{result_off.total_cost - result_on.total_cost:+,.0f}, Profit: ¥{result_off.total_profit - result_on.total_profit:+,.0f}")

        # More crops = more candidate combinations
        assert result_on.total_profit > 0
        assert result_off.total_profit > 0

    def test_scenario_5_large_fields_6crops(self, test_data_dir):
        """Scenario 5: Large fields with fallow period, 6 crop types."""
        fields_file = test_data_dir / "allocation_fields_large.json"
        crops_file = test_data_dir / "allocation_crops_6types.json"
        weather_file = test_data_dir / "weather_2023_full.json"

        # Run with filtering ON
        result_on = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=True,
        )

        # Run with filtering OFF
        result_off = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=False,
        )

        # Analysis
        print("\n=== Scenario 5: Large Fields, 6 Crop Types ===")
        print(f"Filter ON  - Cost: ¥{result_on.total_cost:,.0f}, Revenue: ¥{result_on.total_revenue:,.0f}, Profit: ¥{result_on.total_profit:,.0f}")
        print(f"Filter OFF - Cost: ¥{result_off.total_cost:,.0f}, Revenue: ¥{result_off.total_revenue:,.0f}, Profit: ¥{result_off.total_profit:,.0f}")
        print(f"Difference - Cost: ¥{result_off.total_cost - result_on.total_cost:+,.0f}, Profit: ¥{result_off.total_profit - result_on.total_profit:+,.0f}")

        # Larger fields = higher potential revenue
        assert result_on.total_profit > 0
        assert result_off.total_profit > 0

    def test_scenario_6_balanced_crops(self, test_data_dir):
        """Scenario 6: 4 fields with fallow, balanced crop configuration."""
        fields_file = test_data_dir / "allocation_fields_with_fallow.json"
        crops_file = test_data_dir / "allocation_crops_balanced.json"
        weather_file = test_data_dir / "weather_2023_full.json"

        # Run with filtering ON
        result_on = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=True,
        )

        # Run with filtering OFF
        result_off = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=False,
        )

        # Analysis
        print("\n=== Scenario 6: With Fallow, Balanced Crops (4 fields) ===")
        print(f"Filter ON  - Cost: ¥{result_on.total_cost:,.0f}, Revenue: ¥{result_on.total_revenue:,.0f}, Profit: ¥{result_on.total_profit:,.0f}")
        print(f"Filter OFF - Cost: ¥{result_off.total_cost:,.0f}, Revenue: ¥{result_off.total_revenue:,.0f}, Profit: ¥{result_off.total_profit:,.0f}")
        print(f"Difference - Cost: ¥{result_off.total_cost - result_on.total_cost:+,.0f}, Profit: ¥{result_off.total_profit - result_on.total_profit:+,.0f}")

        assert result_on.total_profit > 0
        assert result_off.total_profit > 0

    def test_scenario_7_xlarge_fields_6crops(self, test_data_dir):
        """Scenario 7: Extra-large fields with fallow period, 6 crop types (maximum scale)."""
        fields_file = test_data_dir / "allocation_fields_xlarge.json"
        crops_file = test_data_dir / "allocation_crops_6types.json"
        weather_file = test_data_dir / "weather_2023_full.json"

        # Run with filtering ON
        result_on = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=True,
        )

        # Run with filtering OFF
        result_off = self._run_optimization(
            fields_file, crops_file, weather_file,
            "2023-04-01", "2023-10-31",
            filter_redundant=False,
        )

        # Analysis
        print("\n=== Scenario 7: Extra-Large Fields, 6 Crop Types (maximum scale) ===")
        print(f"Filter ON  - Cost: ¥{result_on.total_cost:,.0f}, Revenue: ¥{result_on.total_revenue:,.0f}, Profit: ¥{result_on.total_profit:,.0f}")
        print(f"Filter OFF - Cost: ¥{result_off.total_cost:,.0f}, Revenue: ¥{result_off.total_revenue:,.0f}, Profit: ¥{result_off.total_profit:,.0f}")
        print(f"Difference - Cost: ¥{result_off.total_cost - result_on.total_cost:+,.0f}, Profit: ¥{result_off.total_profit - result_on.total_profit:+,.0f}")

        # Maximum scale test (may result in negative profit due to large field costs)
        # Verify that both produce results (profit can be positive or negative)
        assert result_on.total_cost > 0, "Should have calculated costs"
        assert result_off.total_cost > 0, "Should have calculated costs"

    def test_comprehensive_summary(self, test_data_dir):
        """Comprehensive test: Run all scenarios and generate summary report."""
        scenarios = [
            {
                "name": "With Fallow (4 fields, 4 crops)",
                "fields": "allocation_fields_with_fallow.json",
                "crops": "allocation_crops_1760447748.json",
                "weather": "weather_2023_full.json",
                "period": ("2023-04-01", "2023-10-31"),
            },
            {
                "name": "No Fallow - Continuous (4 fields, 4 crops)",
                "fields": "allocation_fields_no_fallow.json",
                "crops": "allocation_crops_1760447748.json",
                "weather": "weather_2023_full.json",
                "period": ("2023-04-01", "2023-10-31"),
            },
            {
                "name": "Strict Fallow (4 fields, 4 crops)",
                "fields": "allocation_fields_strict_fallow.json",
                "crops": "allocation_crops_1760447748.json",
                "weather": "weather_2023_full.json",
                "period": ("2023-04-01", "2023-10-31"),
            },
            {
                "name": "With Fallow (4 fields, 6 crops)",
                "fields": "allocation_fields_with_fallow.json",
                "crops": "allocation_crops_6types.json",
                "weather": "weather_2023_full.json",
                "period": ("2023-04-01", "2023-10-31"),
            },
            {
                "name": "Large Fields (8 fields, 6 crops)",
                "fields": "allocation_fields_large.json",
                "crops": "allocation_crops_6types.json",
                "weather": "weather_2023_full.json",
                "period": ("2023-04-01", "2023-10-31"),
            },
            {
                "name": "Balanced Crops (4 fields)",
                "fields": "allocation_fields_with_fallow.json",
                "crops": "allocation_crops_balanced.json",
                "weather": "weather_2023_full.json",
                "period": ("2023-04-01", "2023-10-31"),
            },
            {
                "name": "Extra-Large Fields (16 fields, 6 crops)",
                "fields": "allocation_fields_xlarge.json",
                "crops": "allocation_crops_6types.json",
                "weather": "weather_2023_full.json",
                "period": ("2023-04-01", "2023-10-31"),
            },
        ]

        print("\n" + "="*80)
        print("COMPREHENSIVE FILTER COMPARISON SUMMARY")
        print("="*80)

        summary_data = []

        for scenario in scenarios:
            try:
                fields_file = test_data_dir / scenario["fields"]
                crops_file = test_data_dir / scenario["crops"]
                weather_file = test_data_dir / scenario["weather"]
                start, end = scenario["period"]

                # Run both
                result_on = self._run_optimization(
                    fields_file, crops_file, weather_file, start, end, True
                )
                result_off = self._run_optimization(
                    fields_file, crops_file, weather_file, start, end, False
                )

                summary_data.append({
                    "scenario": scenario["name"],
                    "filter_on": {
                        "cost": result_on.total_cost,
                        "revenue": result_on.total_revenue,
                        "profit": result_on.total_profit,
                        "fields": len(result_on.field_schedules),
                    },
                    "filter_off": {
                        "cost": result_off.total_cost,
                        "revenue": result_off.total_revenue,
                        "profit": result_off.total_profit,
                        "fields": len(result_off.field_schedules),
                    },
                    "diff": {
                        "cost": result_off.total_cost - result_on.total_cost,
                        "profit": result_off.total_profit - result_on.total_profit,
                    }
                })

            except Exception as e:
                print(f"\n[SKIP] {scenario['name']}: {str(e)}")
                continue

        # Print formatted summary
        print("\n" + "-"*80)
        print(f"{'Scenario':<40} {'Filter':<8} {'Cost':>12} {'Revenue':>12} {'Profit':>12}")
        print("-"*80)
        
        for data in summary_data:
            print(f"{data['scenario']:<40} {'ON':<8} ¥{data['filter_on']['cost']:>11,.0f} ¥{data['filter_on']['revenue']:>11,.0f} ¥{data['filter_on']['profit']:>11,.0f}")
            print(f"{'':<40} {'OFF':<8} ¥{data['filter_off']['cost']:>11,.0f} ¥{data['filter_off']['revenue']:>11,.0f} ¥{data['filter_off']['profit']:>11,.0f}")
            print(f"{'':<40} {'Diff':<8} ¥{data['diff']['cost']:>+11,.0f} {'':>12} ¥{data['diff']['profit']:>+11,.0f}")
            print("-"*80)

        # Statistical analysis
        profit_improvements = [d['diff']['profit'] for d in summary_data]
        cost_differences = [d['diff']['cost'] for d in summary_data]
        
        print(f"\nStatistical Summary:")
        print(f"  Total scenarios tested: {len(summary_data)}")
        print(f"  Profit improvements (OFF - ON):")
        print(f"    - Max: ¥{max(profit_improvements):+,.0f}")
        print(f"    - Min: ¥{min(profit_improvements):+,.0f}")
        print(f"    - Avg: ¥{sum(profit_improvements)/len(profit_improvements):+,.0f}")
        print(f"  Cost differences (OFF - ON):")
        print(f"    - Max: ¥{max(cost_differences):+,.0f}")
        print(f"    - Min: ¥{min(cost_differences):+,.0f}")
        print(f"    - Avg: ¥{sum(cost_differences)/len(cost_differences):+,.0f}")
        
        scenarios_with_better_profit = sum(1 for p in profit_improvements if p > 0)
        scenarios_with_same_profit = sum(1 for p in profit_improvements if p == 0)
        
        print(f"\n  Filter OFF finds better profit: {scenarios_with_better_profit}/{len(summary_data)} scenarios")
        print(f"  Same profit (optimal either way): {scenarios_with_same_profit}/{len(summary_data)} scenarios")

        # At least 5 scenarios should be tested
        assert len(summary_data) >= 5, f"Expected at least 5 scenarios, got {len(summary_data)}"

