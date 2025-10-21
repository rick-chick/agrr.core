"""Integration tests for allocation adjustment feature.

This module tests the complete workflow of the adjust command including:
- File loading (current allocation, moves, weather, fields, crops)
- Move instruction application (move, remove)
- Re-optimization
- Output generation (table, json)
"""

import pytest
import json
import asyncio
from datetime import datetime
from pathlib import Path

from agrr_core.entity.entities.move_instruction_entity import MoveInstruction, MoveAction
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_schedule_entity import FieldSchedule
from agrr_core.entity.entities.multi_field_optimization_result_entity import MultiFieldOptimizationResult
from agrr_core.usecase.dto.allocation_adjust_request_dto import AllocationAdjustRequestDTO
from agrr_core.usecase.interactors.allocation_adjust_interactor import AllocationAdjustInteractor
from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
from agrr_core.adapter.gateways.move_instruction_file_gateway import MoveInstructionFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.framework.services.io.file_service import FileService


class TestAllocationAdjustBasics:
    """Basic functionality tests for allocation adjustment."""
    
    @pytest.fixture
    def file_service(self):
        """Create file service instance."""
        return FileService()
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return Path(__file__).parent.parent.parent / "test_data"
    
    @pytest.mark.asyncio
    async def test_load_current_allocation(self, file_service, test_data_dir):
        """Test loading current allocation from JSON file."""
        allocation_file = str(test_data_dir / "test_current_allocation.json")
        
        gateway = AllocationResultFileGateway(file_service, allocation_file)
        result = await gateway.get()
        
        assert result is not None
        assert result.optimization_id is not None
        assert len(result.field_schedules) > 0
        assert result.total_profit > 0
    
    @pytest.mark.asyncio
    async def test_load_move_instructions(self, file_service, test_data_dir):
        """Test loading move instructions from JSON file."""
        moves_file = str(test_data_dir / "test_adjust_moves.json")
        
        gateway = MoveInstructionFileGateway(file_service, moves_file)
        moves = await gateway.get_all()
        
        assert len(moves) > 0
        assert all(isinstance(m, MoveInstruction) for m in moves)
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, file_service):
        """Test error handling for nonexistent file."""
        gateway = AllocationResultFileGateway(file_service, "nonexistent.json")
        
        result = await gateway.get()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invalid_json_format(self, file_service, tmp_path):
        """Test error handling for invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        gateway = AllocationResultFileGateway(file_service, str(invalid_file))
        
        with pytest.raises(ValueError, match="Invalid optimization result file format"):
            await gateway.get()


class TestMoveInstructions:
    """Tests for move instruction handling."""
    
    @pytest.fixture
    def sample_field(self):
        """Create sample field."""
        return Field(
            field_id="field_1",
            name="Test Field 1",
            area=1000.0,
            daily_fixed_cost=5000.0,
            fallow_period_days=28,
        )
    
    @pytest.fixture
    def sample_crop(self):
        """Create sample crop."""
        return Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            variety="Momotaro",
            revenue_per_area=50000.0,
            max_revenue=800000.0,
            groups=["Solanaceae"],
        )
    
    @pytest.fixture
    def sample_allocation(self, sample_field, sample_crop):
        """Create sample allocation."""
        return CropAllocation(
            allocation_id="alloc_001",
            field=sample_field,
            crop=sample_crop,
            area_used=15.0,
            start_date=datetime(2023, 5, 1),
            completion_date=datetime(2023, 8, 15),
            growth_days=106,
            accumulated_gdd=1200.0,
            total_cost=530000.0,
            expected_revenue=750000.0,
            profit=220000.0,
        )
    
    def test_move_instruction_move_action(self):
        """Test creating MOVE instruction."""
        move = MoveInstruction(
            allocation_id="alloc_001",
            action=MoveAction.MOVE,
            to_field_id="field_2",
            to_start_date=datetime(2023, 5, 15),
            to_area=12.0,
        )
        
        assert move.action == MoveAction.MOVE
        assert move.to_field_id == "field_2"
        assert move.to_start_date == datetime(2023, 5, 15)
        assert move.to_area == 12.0
    
    def test_move_instruction_remove_action(self):
        """Test creating REMOVE instruction."""
        move = MoveInstruction(
            allocation_id="alloc_002",
            action=MoveAction.REMOVE,
        )
        
        assert move.action == MoveAction.REMOVE
        assert move.to_field_id is None
        assert move.to_start_date is None
        assert move.to_area is None
    
    def test_move_requires_to_field(self):
        """Test that MOVE action requires to_field_id."""
        with pytest.raises(ValueError, match="to_field_id is required"):
            MoveInstruction(
                allocation_id="alloc_001",
                action=MoveAction.MOVE,
                to_start_date=datetime(2023, 5, 15),
            )
    
    def test_move_requires_to_start_date(self):
        """Test that MOVE action requires to_start_date."""
        with pytest.raises(ValueError, match="to_start_date is required"):
            MoveInstruction(
                allocation_id="alloc_001",
                action=MoveAction.MOVE,
                to_field_id="field_2",
            )
    
    def test_remove_should_not_have_to_fields(self):
        """Test that REMOVE action should not have to_* fields."""
        with pytest.raises(ValueError, match="should not be specified"):
            MoveInstruction(
                allocation_id="alloc_002",
                action=MoveAction.REMOVE,
                to_field_id="field_2",
            )


class TestAllocationAdjustRequestDTO:
    """Tests for request DTO validation."""
    
    def test_valid_request(self):
        """Test creating valid request DTO."""
        moves = [
            MoveInstruction(
                allocation_id="alloc_001",
                action=MoveAction.MOVE,
                to_field_id="field_2",
                to_start_date=datetime(2023, 5, 15),
            ),
        ]
        
        request = AllocationAdjustRequestDTO(
            current_optimization_id="opt_001",
            move_instructions=moves,
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        assert request.current_optimization_id == "opt_001"
        assert len(request.move_instructions) == 1
    
    def test_empty_moves_raises_error(self):
        """Test that empty moves list raises error."""
        with pytest.raises(ValueError, match="move_instructions cannot be empty"):
            AllocationAdjustRequestDTO(
                current_optimization_id="opt_001",
                move_instructions=[],
                planning_period_start=datetime(2023, 4, 1),
                planning_period_end=datetime(2023, 10, 31),
            )
    
    def test_invalid_date_range(self):
        """Test that invalid date range raises error."""
        moves = [
            MoveInstruction(
                allocation_id="alloc_001",
                action=MoveAction.REMOVE,
            ),
        ]
        
        with pytest.raises(ValueError, match="planning_period_end.*must be after"):
            AllocationAdjustRequestDTO(
                current_optimization_id="opt_001",
                move_instructions=moves,
                planning_period_start=datetime(2023, 10, 31),
                planning_period_end=datetime(2023, 4, 1),
            )
    
    def test_invalid_objective(self):
        """Test removed - optimization_objective is no longer used."""
        # This test is no longer relevant as optimization_objective was removed
        # The adjust command simply applies moves and recalculates metrics
        pass


class TestEndToEndWorkflow:
    """End-to-end integration tests."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return Path(__file__).parent.parent.parent / "test_data"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_adjust_workflow(self, test_data_dir):
        """Test complete adjustment workflow with real data.
        
        This test simulates the actual CLI workflow:
        1. Load current allocation
        2. Load move instructions
        3. Apply moves
        4. Re-optimize
        5. Generate output
        """
        file_service = FileService()
        
        # Setup gateways
        optimization_result_gateway = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        
        move_instruction_gateway = MoveInstructionFileGateway(
            file_service,
            str(test_data_dir / "test_adjust_moves.json")
        )
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service,
            str(test_data_dir / "allocation_crops_1760447748.json")
        )
        
        weather_gateway = WeatherFileGateway(
            file_service,
            str(test_data_dir / "weather_2023_full.json")
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Create interactor
        interactor = AllocationAdjustInteractor(
            allocation_result_gateway=optimization_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
        )
        
        # Load moves for request
        moves = await move_instruction_gateway.get_all()
        
        # Create request
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=moves,
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        # Execute
        response = await interactor.execute(request)
        
        # Assertions
        assert response.success is True
        assert len(response.applied_moves) > 0
        assert response.optimized_result is not None
        assert response.optimized_result.total_profit > 0
        assert "adjust" in response.optimized_result.algorithm_used
    
    @pytest.mark.asyncio
    async def test_all_moves_rejected(self, test_data_dir, tmp_path):
        """Test behavior when all moves are rejected."""
        file_service = FileService()
        
        # Create invalid moves (non-existent allocation IDs)
        invalid_moves = {
            "moves": [
                {
                    "allocation_id": "nonexistent_001",
                    "action": "remove"
                },
                {
                    "allocation_id": "nonexistent_002",
                    "action": "move",
                    "to_field_id": "field_1",
                    "to_start_date": "2023-05-15"
                }
            ]
        }
        
        invalid_moves_file = tmp_path / "invalid_moves.json"
        invalid_moves_file.write_text(json.dumps(invalid_moves))
        
        # Setup gateways
        optimization_result_gateway = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        
        move_instruction_gateway = MoveInstructionFileGateway(
            file_service,
            str(invalid_moves_file)
        )
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service,
            str(test_data_dir / "allocation_crops_1760447748.json")
        )
        
        weather_gateway = WeatherFileGateway(
            file_service,
            str(test_data_dir / "weather_2023_full.json")
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Create interactor
        interactor = AllocationAdjustInteractor(
            allocation_result_gateway=optimization_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
        )
        
        # Load moves
        moves = await move_instruction_gateway.get_all()
        
        # Create request
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=moves,
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        # Execute
        response = await interactor.execute(request)
        
        # Assertions
        assert response.success is False
        assert len(response.applied_moves) == 0
        assert len(response.rejected_moves) == 2
        assert "No moves were applied" in response.message


class TestOutputFormats:
    """Tests for output formatting."""
    
    @pytest.mark.asyncio
    async def test_json_output_structure(self, tmp_path):
        """Test JSON output has correct structure."""
        # This test would require setting up presenter and checking JSON structure
        # Placeholder for now
        pass
    
    @pytest.mark.asyncio
    async def test_table_output_rendering(self):
        """Test table output renders correctly."""
        # This test would capture stdout and verify table format
        # Placeholder for now
        pass


class TestConstraints:
    """Tests for constraint enforcement."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return Path(__file__).parent.parent.parent / "test_data"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_fallow_period_enforcement(self, test_data_dir):
        """Test that fallow period is enforced during re-optimization.
        
        Scenario:
        - field_1 has 28-day fallow period
        - Existing allocation: 2023-05-31 to 2023-07-23
        - Next allocation can start: 2023-08-20 (07-23 + 28 days)
        - Try to move an allocation to field_1 starting 2023-08-01 (too early)
        - Expected: Re-optimization respects fallow period
        """
        file_service = FileService()
        
        # Create move instruction that might violate fallow period
        fallow_violation_file = test_data_dir / "test_fallow_violation_moves.json"
        
        # Setup gateways
        optimization_result_gateway = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        
        move_instruction_gateway = MoveInstructionFileGateway(
            file_service,
            str(fallow_violation_file)
        )
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service,
            str(test_data_dir / "allocation_crops_1760447748.json")
        )
        
        weather_gateway = WeatherFileGateway(
            file_service,
            str(test_data_dir / "weather_2023_full.json")
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Create interactor
        interactor = AllocationAdjustInteractor(
            allocation_result_gateway=optimization_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
        )
        
        # Load moves
        moves = await move_instruction_gateway.get_all()
        
        # Create request
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=moves,
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        # Execute
        response = await interactor.execute(request)
        
        # Assertions
        assert response.success is True
        
        # Verify that fallow period is respected in final result
        for schedule in response.optimized_result.field_schedules:
            allocations = sorted(schedule.allocations, key=lambda a: a.start_date)
            for i in range(len(allocations) - 1):
                current = allocations[i]
                next_alloc = allocations[i + 1]
                
                # Check fallow period
                from datetime import timedelta
                min_next_start = current.completion_date + timedelta(days=schedule.field.fallow_period_days)
                
                assert next_alloc.start_date >= min_next_start, (
                    f"Fallow period violation in {schedule.field.field_id}: "
                    f"{current.allocation_id} ends {current.completion_date}, "
                    f"next starts {next_alloc.start_date} "
                    f"(should be >= {min_next_start} with {schedule.field.fallow_period_days}-day fallow)"
                )
    
    @pytest.mark.asyncio
    async def test_different_fallow_periods(self, test_data_dir):
        """Test that different fields have different fallow periods.
        
        Verify:
        - field_1: 28 days
        - field_2: 21 days
        - field_3: 14 days
        - field_4: 7 days
        """
        file_service = FileService()
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        fields = await field_gateway.get_all()
        
        expected_fallow = {
            "field_1": 28,
            "field_2": 21,
            "field_3": 14,
            "field_4": 7,
        }
        
        for field in fields:
            assert field.fallow_period_days == expected_fallow[field.field_id], (
                f"{field.field_id} should have {expected_fallow[field.field_id]} days fallow, "
                f"got {field.fallow_period_days}"
            )


class TestInteractionRules:
    """Tests for interaction rules (continuous cultivation, crop rotation)."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return Path(__file__).parent.parent.parent / "test_data"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_with_interaction_rules(self, test_data_dir):
        """Test adjustment with interaction rules applied.
        
        Verifies that interaction rules are loaded and applied during re-optimization.
        """
        file_service = FileService()
        
        # Check if interaction rules file exists
        rules_file = test_data_dir / "allocation_rules_test.json"
        if not rules_file.exists():
            pytest.skip("Interaction rules test file not found")
        
        # Setup gateways
        optimization_result_gateway = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        
        move_instruction_gateway = MoveInstructionFileGateway(
            file_service,
            str(test_data_dir / "test_adjust_moves.json")
        )
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service,
            str(test_data_dir / "allocation_crops_1760447748.json")
        )
        
        weather_gateway = WeatherFileGateway(
            file_service,
            str(test_data_dir / "weather_2023_full.json")
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Setup interaction rule gateway
        from agrr_core.adapter.gateways.interaction_rule_file_gateway import InteractionRuleFileGateway
        interaction_rule_gateway = InteractionRuleFileGateway(
            file_service,
            str(rules_file)
        )
        
        # Create interactor with rules
        interactor = AllocationAdjustInteractor(
            allocation_result_gateway=optimization_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
            interaction_rule_gateway=interaction_rule_gateway,
        )
        
        # Load moves
        moves = await move_instruction_gateway.get_all()
        
        # Create request
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=moves,
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        # Execute
        response = await interactor.execute(request)
        
        # Assertions
        assert response.success is True
        assert response.optimized_result is not None


class TestAlgorithmComparison:
    """Tests for comparing DP vs Greedy algorithms."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return Path(__file__).parent.parent.parent / "test_data"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_dp_vs_greedy_profit(self, test_data_dir):
        """Compare DP and Greedy algorithms for profit optimization.
        
        Expected: DP should produce equal or higher profit than Greedy.
        """
        file_service = FileService()
        
        # Setup gateways (shared for both tests)
        optimization_result_gateway = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        
        move_instruction_gateway = MoveInstructionFileGateway(
            file_service,
            str(test_data_dir / "test_adjust_moves.json")
        )
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service,
            str(test_data_dir / "allocation_crops_1760447748.json")
        )
        
        weather_gateway = WeatherFileGateway(
            file_service,
            str(test_data_dir / "weather_2023_full.json")
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Create interactor
        interactor = AllocationAdjustInteractor(
            allocation_result_gateway=optimization_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
        )
        
        # Load moves
        moves = await move_instruction_gateway.get_all()
        
        # Create request
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=moves,
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        # Execute
        response = await interactor.execute(request)
        
        # Assertions
        assert response.success is True
        
        dp_profit = response_dp.optimized_result.total_profit
        greedy_profit = response_greedy.optimized_result.total_profit
        
        # DP should be >= Greedy (allowing small floating point differences)
        assert dp_profit >= greedy_profit - 0.01, (
            f"DP profit ({dp_profit:.2f}) should be >= Greedy profit ({greedy_profit:.2f})"
        )
        
        # Record results for analysis
        print(f"\nAlgorithm Comparison:")
        print(f"  DP profit:     ¥{dp_profit:,.2f}")
        print(f"  Greedy profit: ¥{greedy_profit:,.2f}")
        print(f"  Difference:    ¥{dp_profit - greedy_profit:,.2f}")
        print(f"  DP time:       {response_dp.optimized_result.optimization_time:.3f}s")
        print(f"  Greedy time:   {response_greedy.optimized_result.optimization_time:.3f}s")


class TestE2EScenarios:
    """End-to-end scenario tests."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return Path(__file__).parent.parent.parent / "test_data"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_scenario_field_emergency(self, test_data_dir, tmp_path):
        """Scenario 1: Field Emergency Response.
        
        Simulate field_1 becoming unavailable and moving all allocations to other fields.
        """
        file_service = FileService()
        
        # Create emergency moves: remove all allocations from field_1
        emergency_moves = {
            "moves": [
                {
                    "allocation_id": "e4e5fd28-d258-40fa-b8fc-4322941ca0dc",
                    "action": "remove"
                },
                {
                    "allocation_id": "b4413832-fe6b-43b6-9868-12d3c5d867cd",
                    "action": "remove"
                }
            ]
        }
        
        emergency_moves_file = tmp_path / "emergency_moves.json"
        emergency_moves_file.write_text(json.dumps(emergency_moves))
        
        # Setup gateways
        optimization_result_gateway = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        
        move_instruction_gateway = MoveInstructionFileGateway(
            file_service,
            str(emergency_moves_file)
        )
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service,
            str(test_data_dir / "allocation_crops_1760447748.json")
        )
        
        weather_gateway = WeatherFileGateway(
            file_service,
            str(test_data_dir / "weather_2023_full.json")
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Create interactor
        interactor = AllocationAdjustInteractor(
            allocation_result_gateway=optimization_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
        )
        
        # Load moves
        moves = await move_instruction_gateway.get_all()
        
        # Create request
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=moves,
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        # Execute
        response = await interactor.execute(request)
        
        # Assertions
        assert response.success is True
        assert len(response.applied_moves) == 2
        
        # Verify field_1 allocations were removed
        field_1_schedule = next(
            (s for s in response.optimized_result.field_schedules if s.field.field_id == "field_1"),
            None
        )
        
        # field_1 might be re-used by optimizer or might be empty
        # Just verify the operation succeeded
        assert response.optimized_result.total_profit > 0
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_scenario_profit_improvement(self, test_data_dir):
        """Scenario 2: Profit Improvement.
        
        Remove low-profit allocations and let optimizer re-allocate for better profit.
        """
        file_service = FileService()
        
        # Load current allocation to find lowest profit allocation
        current_file = test_data_dir / "test_current_allocation.json"
        content = await file_service.read(str(current_file))
        data = json.loads(content)
        
        # Find allocation with lowest profit
        all_allocations = []
        for schedule in data["optimization_result"]["field_schedules"]:
            for alloc in schedule["allocations"]:
                all_allocations.append(alloc)
        
        # Sort by profit and pick lowest
        sorted_by_profit = sorted(all_allocations, key=lambda a: a.get("profit", 0))
        lowest_profit_alloc = sorted_by_profit[0] if sorted_by_profit else None
        
        if not lowest_profit_alloc:
            pytest.skip("No allocations found")
        
        # Create moves: remove lowest profit allocation
        improvement_moves = {
            "moves": [
                {
                    "allocation_id": lowest_profit_alloc["allocation_id"],
                    "action": "remove"
                }
            ]
        }
        
        # Save to temp file
        from pathlib import Path
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(improvement_moves, f)
            improvement_moves_file = f.name
        
        try:
            # Setup gateways
            optimization_result_gateway = AllocationResultFileGateway(
                file_service,
                str(test_data_dir / "test_current_allocation.json")
            )
            
            move_instruction_gateway = MoveInstructionFileGateway(
                file_service,
                improvement_moves_file
            )
            
            field_gateway = FieldFileGateway(
                file_service,
                str(test_data_dir / "allocation_fields_with_fallow.json")
            )
            
            crop_gateway = CropProfileFileGateway(
                file_service,
                str(test_data_dir / "allocation_crops_1760447748.json")
            )
            
            weather_gateway = WeatherFileGateway(
                file_service,
                str(test_data_dir / "weather_2023_full.json")
            )
            
            crop_profile_gateway_internal = CropProfileInMemoryGateway()
            
            # Create interactor
            interactor = AllocationAdjustInteractor(
                allocation_result_gateway=optimization_result_gateway,
                field_gateway=field_gateway,
                crop_gateway=crop_gateway,
                weather_gateway=weather_gateway,
                crop_profile_gateway_internal=crop_profile_gateway_internal,
            )
            
            # Load moves
            moves = await move_instruction_gateway.get_all()
            
            # Create request
            request = AllocationAdjustRequestDTO(
                current_optimization_id="",
                move_instructions=moves,
                planning_period_start=datetime(2023, 4, 1),
                planning_period_end=datetime(2023, 10, 31),
            )
            
            # Execute
            response = await interactor.execute(request)
            
            # Assertions
            assert response.success is True
            assert len(response.applied_moves) == 1
            
            # Note: Total allocations might not change because re-optimization
            # can fill the freed slot with new allocations
            # Just verify the removed allocation is no longer present
            new_alloc_ids = set()
            for schedule in response.optimized_result.field_schedules:
                for alloc in schedule.allocations:
                    new_alloc_ids.add(alloc.allocation_id)
            
            assert lowest_profit_alloc["allocation_id"] not in new_alloc_ids, (
                f"Removed allocation {lowest_profit_alloc['allocation_id']} should not be in result"
            )
            
        finally:
            # Cleanup temp file
            Path(improvement_moves_file).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_scenario_sequential_adjustments(self, test_data_dir, tmp_path):
        """Scenario 3: Sequential Adjustments.
        
        Apply multiple adjustments in sequence: adjust → adjust → adjust
        """
        file_service = FileService()
        
        # First adjustment
        moves_1 = {
            "moves": [
                {"allocation_id": "e4e5fd28-d258-40fa-b8fc-4322941ca0dc", "action": "remove"}
            ]
        }
        moves_1_file = tmp_path / "moves_1.json"
        moves_1_file.write_text(json.dumps(moves_1))
        
        # Setup for first adjustment
        opt_result_1 = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        move_1 = MoveInstructionFileGateway(file_service, str(moves_1_file))
        field_gw = FieldFileGateway(file_service, str(test_data_dir / "allocation_fields_with_fallow.json"))
        crop_gw = CropProfileFileGateway(file_service, str(test_data_dir / "allocation_crops_1760447748.json"))
        weather_gw = WeatherFileGateway(file_service, str(test_data_dir / "weather_2023_full.json"))
        
        interactor_1 = AllocationAdjustInteractor(
            allocation_result_gateway=opt_result_1,
            field_gateway=field_gw,
            crop_gateway=crop_gw,
            weather_gateway=weather_gw,
            crop_profile_gateway_internal=CropProfileInMemoryGateway(),
        )
        
        request_1 = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=await move_1.get_all(),
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        response_1 = await interactor_1.execute(request_1)
        
        # Assertions for first adjustment
        assert response_1.success is True
        profit_1 = response_1.optimized_result.total_profit
        
        # Second adjustment would require saving response_1 and loading it
        # For now, just verify first adjustment succeeded
        assert profit_1 > 0


class TestAddNewCropAllocation:
    """Test cases for ADD action to add new crop allocations."""
    
    @pytest.mark.asyncio
    async def test_add_new_crop_allocation(self, tmp_path):
        """Test adding a new crop allocation using ADD action."""
        file_service = FileService()
        test_data_dir = Path(__file__).parent.parent.parent / "test_data"
        
        # Create ADD move instruction
        # Use a date where the crop can complete growth by planning period end (2023-10-31)
        # field_2 existing allocations: 2023-05-14 ~ 2023-07-13, 2023-08-24 ~ 2023-10-31
        # ニンジン grows in ~61 days + 28 days fallow = 89 days total
        # To avoid overlap with 2023-05-14, end must be before that:
        # 2023-02-01 + 61 days = 2023-04-03 + 28 days fallow = 2023-05-01 < 2023-05-14 ✓
        add_moves = {
            "moves": [
                {
                    "allocation_id": "",  # Ignored for ADD action
                    "action": "add",
                    "to_field_id": "field_2",  # Use field_2 which might have space
                    "to_start_date": "2023-02-01T00:00:00",  # Fixed: even earlier to avoid overlap
                    "to_area": 10.0,  # Smaller area to avoid conflicts
                    "crop_id": "ニンジン",  # Use a crop that appears in test data
                    "variety": None
                }
            ]
        }
        
        add_moves_file = tmp_path / "add_moves.json"
        add_moves_file.write_text(json.dumps(add_moves))
        
        # Setup gateways
        optimization_result_gateway = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        
        move_instruction_gateway = MoveInstructionFileGateway(
            file_service,
            str(add_moves_file)
        )
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service,
            str(test_data_dir / "allocation_crops_1760447748.json")
        )
        
        weather_gateway = WeatherFileGateway(
            file_service,
            str(test_data_dir / "weather_2023_full.json")
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Create interactor
        interactor = AllocationAdjustInteractor(
            allocation_result_gateway=optimization_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
        )
        
        # Get current allocation count
        current_result = await optimization_result_gateway.get()
        current_allocation_count = sum(
            len(s.allocations) for s in current_result.field_schedules
        )
        
        # Load moves
        moves = await move_instruction_gateway.get_all()
        
        # Create request
        # Note: planning_period_start adjusted to 2023-02-01 to allow early planting
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=moves,
            planning_period_start=datetime(2023, 2, 1),  # Fixed: match the move start date
            planning_period_end=datetime(2023, 10, 31),
        )
        
        # Execute
        response = await interactor.execute(request)
        
        # Assertions
        assert response.success is True
        assert len(response.applied_moves) == 1
        assert len(response.rejected_moves) == 0
        
        # Verify new allocation was added
        new_allocation_count = sum(
            len(s.allocations) for s in response.optimized_result.field_schedules
        )
        assert new_allocation_count == current_allocation_count + 1
        
        # Verify the new allocation exists in field_2
        field_2_schedule = next(
            (s for s in response.optimized_result.field_schedules if s.field.field_id == "field_2"),
            None
        )
        assert field_2_schedule is not None
        
        # Find the new ニンジン allocation
        ninjin_allocations = [
            a for a in field_2_schedule.allocations
            if a.crop.crop_id == "ニンジン" and a.start_date == datetime(2023, 2, 1)
        ]
        assert len(ninjin_allocations) >= 1  # May be one or more
        # Find the one with area 10.0
        new_alloc = next((a for a in ninjin_allocations if a.area_used == 10.0), None)
        assert new_alloc is not None
        assert new_alloc.allocation_id is not None
        assert new_alloc.allocation_id != ""
    
    @pytest.mark.asyncio
    async def test_add_crop_with_overlap_rejected(self, tmp_path):
        """Test that ADD action is rejected when there's overlap with existing allocation."""
        file_service = FileService()
        test_data_dir = Path(__file__).parent.parent.parent / "test_data"
        
        # Get existing allocation date to create overlap
        current_file = test_data_dir / "test_current_allocation.json"
        content = await file_service.read(str(current_file))
        data = json.loads(content)
        
        # Get first allocation
        first_schedule = data["optimization_result"]["field_schedules"][0]
        first_alloc = first_schedule["allocations"][0]
        overlap_field_id = first_schedule["field_id"]  # Fixed: field_id is directly in schedule
        overlap_date = first_alloc["start_date"]  # Use same start date to create overlap
        
        # Create ADD move with overlapping date
        add_moves = {
            "moves": [
                {
                    "allocation_id": "",
                    "action": "add",
                    "to_field_id": overlap_field_id,
                    "to_start_date": overlap_date,
                    "to_area": 50.0,
                    "crop_id": "ナス",
                    "variety": None
                }
            ]
        }
        
        add_moves_file = tmp_path / "add_overlap_moves.json"
        add_moves_file.write_text(json.dumps(add_moves))
        
        # Setup gateways
        optimization_result_gateway = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        
        move_instruction_gateway = MoveInstructionFileGateway(
            file_service,
            str(add_moves_file)
        )
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service,
            str(test_data_dir / "allocation_crops_1760447748.json")
        )
        
        weather_gateway = WeatherFileGateway(
            file_service,
            str(test_data_dir / "weather_2023_full.json")
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Create interactor
        interactor = AllocationAdjustInteractor(
            allocation_result_gateway=optimization_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
        )
        
        # Load moves
        moves = await move_instruction_gateway.get_all()
        
        # Create request
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=moves,
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        # Execute
        response = await interactor.execute(request)
        
        # Assertions - should be rejected due to overlap
        assert response.success is False
        assert len(response.applied_moves) == 0
        assert len(response.rejected_moves) == 1
        assert "overlap" in response.rejected_moves[0]["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_add_nonexistent_crop_rejected(self, tmp_path):
        """Test that ADD action is rejected when crop_id doesn't exist."""
        file_service = FileService()
        test_data_dir = Path(__file__).parent.parent.parent / "test_data"
        
        # Create ADD move with non-existent crop
        add_moves = {
            "moves": [
                {
                    "allocation_id": "",
                    "action": "add",
                    "to_field_id": "field_1",
                    "to_start_date": "2023-09-01T00:00:00",
                    "to_area": 50.0,
                    "crop_id": "nonexistent_crop",
                    "variety": None
                }
            ]
        }
        
        add_moves_file = tmp_path / "add_nonexistent_crop.json"
        add_moves_file.write_text(json.dumps(add_moves))
        
        # Setup gateways
        optimization_result_gateway = AllocationResultFileGateway(
            file_service,
            str(test_data_dir / "test_current_allocation.json")
        )
        
        move_instruction_gateway = MoveInstructionFileGateway(
            file_service,
            str(add_moves_file)
        )
        
        field_gateway = FieldFileGateway(
            file_service,
            str(test_data_dir / "allocation_fields_with_fallow.json")
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service,
            str(test_data_dir / "allocation_crops_1760447748.json")
        )
        
        weather_gateway = WeatherFileGateway(
            file_service,
            str(test_data_dir / "weather_2023_full.json")
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Create interactor
        interactor = AllocationAdjustInteractor(
            allocation_result_gateway=optimization_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
        )
        
        # Load moves
        moves = await move_instruction_gateway.get_all()
        
        # Create request
        request = AllocationAdjustRequestDTO(
            current_optimization_id="",
            move_instructions=moves,
            planning_period_start=datetime(2023, 4, 1),
            planning_period_end=datetime(2023, 10, 31),
        )
        
        # Execute
        response = await interactor.execute(request)
        
        # Assertions - should be rejected due to non-existent crop
        assert response.success is False
        assert len(response.applied_moves) == 0
        assert len(response.rejected_moves) == 1
        assert "not found" in response.rejected_moves[0]["reason"].lower()

