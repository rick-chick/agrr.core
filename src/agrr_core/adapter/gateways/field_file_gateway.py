"""Field file gateway implementation.

This gateway directly implements FieldGateway interface for file-based field data access.
"""

from typing import List, Dict, Any, Optional

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.exceptions.file_error import FileError
from agrr_core.adapter.interfaces.io.file_service_interface import FileServiceInterface
from agrr_core.usecase.gateways.field_gateway import FieldGateway


class FieldFileGateway(FieldGateway):
    """Gateway for reading field data from files.
    
    Reads field configurations from JSON files.
    Directly implements FieldGateway interface without intermediate layers.
    
    JSON Format:
      Single field:
        {
          "field_id": "field_01",
          "name": "北圃場",
          "area": 1000.0,
          "daily_fixed_cost": 5000.0,
          "location": "北区画"  // optional
        }
      
      Multiple fields:
        {
          "fields": [
            {
              "field_id": "field_01",
              "name": "北圃場",
              "area": 1000.0,
              "daily_fixed_cost": 5000.0,
              "location": "北区画"
            },
            ...
          ]
        }
    """
    
    def __init__(self, file_repository: FileServiceInterface, file_path: str = ""):
        """Initialize field file gateway.
        
        Args:
            file_repository: File repository interface for file I/O operations
            file_path: Path to the fields JSON file
        """
        self.file_repository = file_repository
        self.file_path = file_path
        self._fields_cache: Optional[Dict[str, Field]] = None
    
    async def get(self, field_id: str) -> Optional[Field]:
        """Get field by ID.
        
        Implementation of FieldGateway interface.
        
        Args:
            field_id: Field identifier
            
        Returns:
            Field entity if found, None otherwise
        """
        # Load fields into cache if not already loaded
        if self._fields_cache is None:
            await self._load_fields_cache()
        
        return self._fields_cache.get(field_id) if self._fields_cache else None
    
    async def get_all(self) -> List[Field]:
        """Get all fields from configured source.
        
        Implementation of FieldGateway interface.
        
        Returns:
            List of Field entities
        """
        # Load fields into cache if not already loaded
        if self._fields_cache is None:
            await self._load_fields_cache()
        
        return list(self._fields_cache.values()) if self._fields_cache else []
    
    async def _load_fields_cache(self) -> None:
        """Load all fields from file into cache."""
        if not self.file_path:
            self._fields_cache = {}
            return
        
        fields = await self.read_fields_from_file(self.file_path)
        self._fields_cache = {field.field_id: field for field in fields}
    
    async def read_fields_from_file(self, file_path: str) -> List[Field]:
        """Read field data from JSON file.
        
        Args:
            file_path: Path to the JSON file containing field data
            
        Returns:
            List of Field entities
            
        Raises:
            FileError: If file not found, invalid JSON, or missing required fields
        """
        try:
            if not self.file_repository.exists(file_path):
                raise FileError(f"File not found: {file_path}")
            
            # Read and parse JSON
            content = await self.file_repository.read(file_path)
            import json
            data = json.loads(content)
            
            fields = []
            
            # Handle different JSON structures
            if isinstance(data, dict):
                if 'fields' in data:
                    # Multiple fields format
                    field_list = data['fields']
                else:
                    # Single field format
                    field_list = [data]
            elif isinstance(data, list):
                # Direct array format
                field_list = data
            else:
                raise FileError("Invalid JSON structure. Expected object or array.")
            
            # Convert each field data to Field entity
            for field_data in field_list:
                field = self._convert_dict_to_field(field_data)
                fields.append(field)
            
            return fields
            
        except FileError:
            raise
        except json.JSONDecodeError as e:
            raise FileError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise FileError(f"Failed to read field data from file {file_path}: {e}")
    
    async def get_field_by_id(self, file_path: str, field_id: str) -> Optional[Field]:
        """Get a specific field by ID from file.
        
        Args:
            file_path: Path to the JSON file containing field data
            field_id: Field identifier to search for
            
        Returns:
            Field entity if found, None otherwise
            
        Raises:
            FileError: If file not found or invalid format
        """
        fields = await self.read_fields_from_file(file_path)
        
        for field in fields:
            if field.field_id == field_id:
                return field
        
        return None
    
    def _convert_dict_to_field(self, data: Dict[str, Any]) -> Field:
        """Convert dictionary to Field entity.
        
        Args:
            data: Dictionary containing field data
            
        Returns:
            Field entity
            
        Raises:
            FileError: If required fields are missing or invalid
        """
        # Validate field data
        if not self.validate_field_data(data):
            missing_fields = []
            for field in ['field_id', 'name', 'area', 'daily_fixed_cost']:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                raise FileError(f"Missing required field(s): {', '.join(missing_fields)}")
            
            # Check for negative values
            if data.get('area', 0) < 0:
                raise FileError("Field 'area' must be non-negative")
            if data.get('daily_fixed_cost', 0) < 0:
                raise FileError("Field 'daily_fixed_cost' must be non-negative")
        
        try:
            return Field(
                field_id=str(data['field_id']),
                name=str(data['name']),
                area=float(data['area']),
                daily_fixed_cost=float(data['daily_fixed_cost']),
                location=str(data['location']) if 'location' in data and data['location'] is not None else None
            )
        except (KeyError, ValueError, TypeError) as e:
            raise FileError(f"Invalid field data: {e}")
    
    def validate_field_data(self, data: Dict[str, Any]) -> bool:
        """Validate field data dictionary.
        
        Args:
            data: Dictionary containing field data
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ['field_id', 'name', 'area', 'daily_fixed_cost']
        for field in required_fields:
            if field not in data:
                return False
        
        # Check data types and values
        try:
            # field_id and name can be any type that converts to string
            str(data['field_id'])
            str(data['name'])
            
            # area and daily_fixed_cost must be numeric and non-negative
            area = float(data['area'])
            daily_fixed_cost = float(data['daily_fixed_cost'])
            
            if area < 0 or daily_fixed_cost < 0:
                return False
            
            # location is optional, but if present should be string-convertible
            if 'location' in data and data['location'] is not None:
                str(data['location'])
            
            return True
            
        except (ValueError, TypeError):
            return False

