"""Tests for MoveInstruction entity."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.move_instruction_entity import MoveInstruction, MoveAction


class TestMoveInstruction:
    """Test cases for MoveInstruction entity."""
    
    def test_create_move_instruction_move_action(self):
        """Test creating a move instruction with MOVE action."""
        move = MoveInstruction(
            allocation_id="alloc_001",
            action=MoveAction.MOVE,
            to_field_id="field_2",
            to_start_date=datetime(2024, 5, 15),
            to_area=12.0,
        )
        
        assert move.allocation_id == "alloc_001"
        assert move.action == MoveAction.MOVE
        assert move.to_field_id == "field_2"
        assert move.to_start_date == datetime(2024, 5, 15)
        assert move.to_area == 12.0
    
    def test_create_move_instruction_remove_action(self):
        """Test creating a move instruction with REMOVE action."""
        move = MoveInstruction(
            allocation_id="alloc_002",
            action=MoveAction.REMOVE,
        )
        
        assert move.allocation_id == "alloc_002"
        assert move.action == MoveAction.REMOVE
        assert move.to_field_id is None
        assert move.to_start_date is None
        assert move.to_area is None
    
    def test_move_action_requires_to_field_id(self):
        """Test that MOVE action requires to_field_id."""
        with pytest.raises(ValueError, match="to_field_id is required for MOVE action"):
            MoveInstruction(
                allocation_id="alloc_001",
                action=MoveAction.MOVE,
                to_start_date=datetime(2024, 5, 15),
            )
    
    def test_move_action_requires_to_start_date(self):
        """Test that MOVE action requires to_start_date."""
        with pytest.raises(ValueError, match="to_start_date is required for MOVE action"):
            MoveInstruction(
                allocation_id="alloc_001",
                action=MoveAction.MOVE,
                to_field_id="field_2",
            )
    
    def test_move_action_with_invalid_area(self):
        """Test that MOVE action with invalid area raises error."""
        with pytest.raises(ValueError, match="to_area must be positive"):
            MoveInstruction(
                allocation_id="alloc_001",
                action=MoveAction.MOVE,
                to_field_id="field_2",
                to_start_date=datetime(2024, 5, 15),
                to_area=-10.0,
            )
    
    def test_remove_action_with_to_fields_raises_error(self):
        """Test that REMOVE action with to_* fields raises error."""
        with pytest.raises(ValueError, match="to_\\* fields should not be specified for REMOVE action"):
            MoveInstruction(
                allocation_id="alloc_002",
                action=MoveAction.REMOVE,
                to_field_id="field_2",
            )
    
    def test_move_instruction_is_frozen(self):
        """Test that MoveInstruction is immutable."""
        move = MoveInstruction(
            allocation_id="alloc_001",
            action=MoveAction.MOVE,
            to_field_id="field_2",
            to_start_date=datetime(2024, 5, 15),
        )
        
        with pytest.raises(AttributeError):
            move.allocation_id = "alloc_002"

