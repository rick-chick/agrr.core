"""Move instruction file gateway implementation.

Gateway implementation for loading move instructions from JSON files.
"""

import json
from typing import List
from datetime import datetime

from agrr_core.usecase.gateways.move_instruction_gateway import MoveInstructionGateway
from agrr_core.entity.entities.move_instruction_entity import MoveInstruction, MoveAction
from agrr_core.adapter.interfaces.io.file_service_interface import FileServiceInterface


class MoveInstructionFileGateway(MoveInstructionGateway):
    """File-based gateway for move instruction operations."""
    
    def __init__(
        self,
        file_repository: FileServiceInterface,
        file_path: str = "",
    ):
        """Initialize with file repository and file path.
        
        Args:
            file_repository: File service for file I/O operations
            file_path: Path to the move instructions JSON file
        """
        self.file_repository = file_repository
        self.file_path = file_path
    
    async def get_all(self) -> List[MoveInstruction]:
        """Get all move instructions from configured source (file in this implementation).
        
        Expected JSON format:
        {
          "moves": [
            {
              "allocation_id": "alloc_001",
              "action": "move",
              "to_field_id": "field_2",
              "to_start_date": "2024-05-15",
              "to_area": 12.0
            },
            {
              "allocation_id": "alloc_002",
              "action": "remove"
            }
          ]
        }
        
        Returns:
            List of move instruction entities
        """
        if not self.file_path:
            return []
        
        try:
            # Read JSON file
            content = await self.file_repository.read(self.file_path)
            data = json.loads(content)
            
            # Parse JSON to entities
            if "moves" not in data:
                raise ValueError("Missing 'moves' field in JSON")
            
            moves = []
            for move_data in data["moves"]:
                # Parse action
                action_str = move_data.get("action", "").lower()
                if action_str == "move":
                    action = MoveAction.MOVE
                elif action_str == "remove":
                    action = MoveAction.REMOVE
                else:
                    raise ValueError(f"Invalid action: {action_str}. Must be 'move' or 'remove'")
                
                # Parse optional fields
                to_field_id = move_data.get("to_field_id")
                to_start_date = None
                if "to_start_date" in move_data:
                    date_str = move_data["to_start_date"]
                    # Support multiple date formats
                    try:
                        to_start_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except ValueError:
                        # Try YYYY-MM-DD format
                        to_start_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                to_area = move_data.get("to_area")
                if to_area is not None:
                    to_area = float(to_area)
                
                # Create move instruction entity
                move = MoveInstruction(
                    allocation_id=move_data["allocation_id"],
                    action=action,
                    to_field_id=to_field_id,
                    to_start_date=to_start_date,
                    to_area=to_area,
                )
                moves.append(move)
            
            return moves
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Move instructions file not found: {self.file_path}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Invalid move instructions file format: {e}")

