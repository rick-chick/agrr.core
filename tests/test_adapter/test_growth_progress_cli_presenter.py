"""Tests for GrowthProgressCLIPresenter."""

import pytest
from datetime import datetime
from io import StringIO
import sys

from agrr_core.adapter.presenters.growth_progress_cli_presenter import (
    GrowthProgressCLIPresenter,
)
from agrr_core.usecase.dto.growth_progress_calculate_response_dto import (
    GrowthProgressCalculateResponseDTO,
    GrowthProgressRecordDTO,
)


class TestGrowthProgressCLIPresenter:
    """Test cases for GrowthProgressCLIPresenter."""

    def test_presenter_implements_output_port(self):
        """Test that presenter implements Output Port interface."""
        from agrr_core.usecase.ports.output.growth_progress_calculate_output_port import (
            GrowthProgressCalculateOutputPort,
        )
        
        presenter = GrowthProgressCLIPresenter(output_format="table")
        assert isinstance(presenter, GrowthProgressCalculateOutputPort)

    def test_present_table_format(self, capsys):
        """Test table format output."""
        presenter = GrowthProgressCLIPresenter(output_format="table")
        
        # Create test data
        records = [
            GrowthProgressRecordDTO(
                date=datetime(2024, 5, 1),
                cumulative_gdd=15.0,
                total_required_gdd=1000.0,
                growth_percentage=1.5,
                stage_name="Vegetative",
                is_complete=False,
            ),
            GrowthProgressRecordDTO(
                date=datetime(2024, 5, 2),
                cumulative_gdd=30.0,
                total_required_gdd=1000.0,
                growth_percentage=3.0,
                stage_name="Vegetative",
                is_complete=False,
            ),
        ]
        
        response = GrowthProgressCalculateResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            start_date=datetime(2024, 5, 1),
            progress_records=records,
        )
        
        # Present
        presenter.present(response)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Assertions
        assert "Growth Progress for Rice" in captured.out
        assert "Koshihikari" in captured.out
        assert "2024-05-01" in captured.out
        assert "Vegetative" in captured.out
        assert "1.5%" in captured.out
        assert "3.0%" in captured.out

    def test_present_json_format(self, capsys):
        """Test JSON format output."""
        presenter = GrowthProgressCLIPresenter(output_format="json")
        
        # Create test data
        records = [
            GrowthProgressRecordDTO(
                date=datetime(2024, 5, 1),
                cumulative_gdd=15.0,
                total_required_gdd=1000.0,
                growth_percentage=1.5,
                stage_name="Vegetative",
                is_complete=False,
            ),
        ]
        
        response = GrowthProgressCalculateResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            start_date=datetime(2024, 5, 1),
            progress_records=records,
        )
        
        # Present
        presenter.present(response)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Assertions - should be valid JSON
        import json
        output_data = json.loads(captured.out)
        assert output_data["crop_name"] == "Rice"
        assert output_data["variety"] == "Koshihikari"
        assert len(output_data["progress_records"]) == 1

    def test_get_output_returns_dict(self):
        """Test get_output method returns dictionary."""
        presenter = GrowthProgressCLIPresenter(output_format="table")
        
        records = [
            GrowthProgressRecordDTO(
                date=datetime(2024, 5, 1),
                cumulative_gdd=15.0,
                total_required_gdd=1000.0,
                growth_percentage=1.5,
                stage_name="Vegetative",
                is_complete=False,
            ),
        ]
        
        response = GrowthProgressCalculateResponseDTO(
            crop_name="Rice",
            variety=None,
            start_date=datetime(2024, 5, 1),
            progress_records=records,
        )
        
        presenter.present(response)
        output = presenter.get_output()
        
        # Assertions
        assert isinstance(output, dict)
        assert output["crop_name"] == "Rice"
        assert len(output["progress_records"]) == 1

    def test_present_without_variety(self, capsys):
        """Test presenting data without variety."""
        presenter = GrowthProgressCLIPresenter(output_format="table")
        
        response = GrowthProgressCalculateResponseDTO(
            crop_name="Rice",
            variety=None,  # No variety
            start_date=datetime(2024, 5, 1),
            progress_records=[],
        )
        
        presenter.present(response)
        captured = capsys.readouterr()
        
        # Should not show "Variety:" line
        assert "Growth Progress for Rice" in captured.out
        assert "Variety:" not in captured.out or "Variety: None" not in captured.out

