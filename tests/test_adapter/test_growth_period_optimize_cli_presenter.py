"""Tests for GrowthPeriodOptimizeCliPresenter."""

import pytest
from datetime import datetime
from io import StringIO
import sys
import json

from agrr_core.adapter.presenters.growth_period_optimize_cli_presenter import (
    GrowthPeriodOptimizeCliPresenter,
)
from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    OptimalGrowthPeriodResponseDTO,
    CandidateResultDTO,
)
from agrr_core.entity.entities.field_entity import Field


class TestGrowthPeriodOptimizeCliPresenter:
    """Test cases for GrowthPeriodOptimizeCliPresenter."""

    def test_present_table_format(self, capsys):
        """Test table format output."""
        # Create response DTO
        candidates = [
            CandidateResultDTO(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 4, 10),
                growth_days=10,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=1000.0),
                is_optimal=False,
            ),
            CandidateResultDTO(
                start_date=datetime(2024, 4, 5),
                completion_date=datetime(2024, 4, 10),
                growth_days=6,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=600.0),
                is_optimal=True,
            ),
        ]

        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
            location="Test Location"
        )
        
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 5),
            completion_date=datetime(2024, 4, 10),
            growth_days=6,
            total_cost=6000.0,
            daily_fixed_cost=1000.0,
            field=test_field,
            candidates=candidates,
        )

        # Present
        presenter = GrowthPeriodOptimizeCliPresenter(output_format="table")
        presenter.present(response)

        # Capture output
        captured = capsys.readouterr()
        output = captured.out

        # Assertions
        assert "Optimal Growth Period Analysis" in output
        assert "Rice (Koshihikari)" in output
        assert "Daily Fixed Cost: ¥1,000" in output
        assert "Optimal Solution:" in output
        assert "Start Date: 2024-04-05" in output
        assert "Completion Date: 2024-04-10" in output
        assert "Growth Days: 6 days" in output
        assert "Total Cost: ¥6,000" in output
        assert "All Candidates:" in output
        assert "2024-04-01" in output
        assert "2024-04-05" in output
        assert "← OPTIMAL" in output

    def test_present_table_format_without_variety(self, capsys):
        """Test table format output without variety."""
        candidates = [
            CandidateResultDTO(
                start_date=datetime(2024, 5, 1),
                completion_date=datetime(2024, 5, 5),
                growth_days=5,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=500.0),
                is_optimal=True,
            ),
        ]

        test_field = Field(
            field_id="test_field2",
            name="Test Field 2",
            area=1000.0,
            daily_fixed_cost=500.0,
        )
        
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Tomato",
            variety=None,
            optimal_start_date=datetime(2024, 5, 1),
            completion_date=datetime(2024, 5, 5),
            growth_days=5,
            total_cost=2500.0,
            daily_fixed_cost=500.0,
            field=test_field,
            candidates=candidates,
        )

        presenter = GrowthPeriodOptimizeCliPresenter(output_format="table")
        presenter.present(response)

        captured = capsys.readouterr()
        output = captured.out

        assert "Crop: Tomato" in output
        assert "Koshihikari" not in output  # Should not have variety
        assert "Daily Fixed Cost: ¥500" in output

    def test_present_json_format(self, capsys):
        """Test JSON format output."""
        candidates = [
            CandidateResultDTO(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 4, 10),
                growth_days=10,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=1000.0),
                is_optimal=False,
            ),
            CandidateResultDTO(
                start_date=datetime(2024, 4, 5),
                completion_date=datetime(2024, 4, 10),
                growth_days=6,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=600.0),
                is_optimal=True,
            ),
        ]

        test_field = Field(
            field_id="test_field3",
            name="Test Field 3",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 5),
            completion_date=datetime(2024, 4, 10),
            growth_days=6,
            total_cost=6000.0,
            daily_fixed_cost=1000.0,
            field=test_field,
            candidates=candidates,
        )

        presenter = GrowthPeriodOptimizeCliPresenter(output_format="json")
        presenter.present(response)

        captured = capsys.readouterr()
        output = captured.out

        # Parse JSON
        parsed = json.loads(output)

        assert parsed["crop_name"] == "Rice"
        assert parsed["variety"] == "Koshihikari"
        assert parsed["optimal_start_date"] == "2024-04-05T00:00:00"
        assert parsed["completion_date"] == "2024-04-10T00:00:00"
        assert parsed["growth_days"] == 6
        assert parsed["total_cost"] == 6000.0
        assert parsed["daily_fixed_cost"] == 1000.0
        assert len(parsed["candidates"]) == 2

    def test_present_with_incomplete_candidate(self, capsys):
        """Test presentation with a candidate that didn't complete."""
        candidates = [
            CandidateResultDTO(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 4, 10),
                growth_days=10,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=1000.0),
                is_optimal=True,
            ),
            CandidateResultDTO(
                start_date=datetime(2024, 4, 15),
                completion_date=None,  # Didn't complete
                growth_days=None,
                field=None,
                is_optimal=False,
            ),
        ]

        test_field = Field(
            field_id="test_field4",
            name="Test Field 4",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety=None,
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 4, 10),
            growth_days=10,
            total_cost=10000.0,
            daily_fixed_cost=1000.0,
            field=test_field,
            candidates=candidates,
        )

        presenter = GrowthPeriodOptimizeCliPresenter(output_format="table")
        presenter.present(response)

        captured = capsys.readouterr()
        output = captured.out

        assert "2024-04-01" in output
        assert "2024-04-15" in output
        assert "N/A" in output  # Should show N/A for incomplete candidate

    def test_get_output(self):
        """Test get_output method."""
        candidates = [
            CandidateResultDTO(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 4, 10),
                growth_days=10,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=1000.0),
                is_optimal=True,
            ),
        ]

        test_field = Field(
            field_id="test_field5",
            name="Test Field 5",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )
        
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 4, 10),
            growth_days=10,
            total_cost=10000.0,
            daily_fixed_cost=1000.0,
            field=test_field,
            candidates=candidates,
        )

        presenter = GrowthPeriodOptimizeCliPresenter()
        presenter.present(response)

        output = presenter.get_output()

        assert output["crop_name"] == "Rice"
        assert output["variety"] == "Koshihikari"
        assert output["growth_days"] == 10

