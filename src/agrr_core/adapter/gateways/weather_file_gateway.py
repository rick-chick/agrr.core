"""Weather file gateway implementation.

This gateway directly implements WeatherGateway interface for file-based weather data access.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.file_error import FileError
from agrr_core.adapter.interfaces.io.file_service_interface import FileServiceInterface
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.framework.validation.output_validator import OutputValidator, OutputValidationError


class WeatherFileGateway(WeatherGateway):
    """File-based implementation of WeatherGateway.
    
    Reads weather data from JSON/CSV files.
    File path is configured at initialization.
    Directly implements WeatherGateway interface without intermediate layers.
    """
    
    def __init__(self, file_repository: FileServiceInterface, file_path: str):
        """Initialize weather file gateway.
        
        Args:
            file_repository: File repository for file I/O operations (Framework layer)
            file_path: File path to weather data file
        """
        self.file_repository = file_repository
        self.file_path = file_path
    
    async def get(self) -> List[WeatherData]:
        """Get weather data from configured file.
        
        Returns:
            List of WeatherData entities
        """
        return await self.read_weather_data_from_file(self.file_path)
    
    async def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create weather data at destination.
        
        Raises:
            NotImplementedError: Weather data creation not implemented in file gateway
        """
        raise NotImplementedError("Weather data creation not implemented in WeatherFileGateway")
    
    async def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
        """Get weather data by location and date range.
        
        Note: File-based weather data doesn't support location-based queries.
        Use API gateway for location-based queries.
        
        Raises:
            NotImplementedError: File gateway doesn't support location queries
        """
        raise NotImplementedError(
            "File-based weather data doesn't support location queries. "
            "Use WeatherAPIGateway or WeatherJMAGateway instead."
        )
    
    async def get_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherDataWithLocationDTO:
        """Get weather forecast.
        
        Note: File-based weather data doesn't support forecast queries.
        Use API gateway for forecast queries.
        
        Raises:
            NotImplementedError: File gateway doesn't support forecast queries
        """
        raise NotImplementedError(
            "File-based weather data doesn't support forecast queries. "
            "Use WeatherAPIGateway instead."
        )
    
    # ===== Reading Methods =====
    
    async def read_weather_data_from_file(self, file_path: str) -> List[WeatherData]:
        """Read weather data from JSON or CSV file."""
        try:
            if not self.file_repository.exists(file_path):
                raise FileError(f"File not found: {file_path}")
            
            # Determine file format by extension
            from pathlib import Path
            path = Path(file_path)
            extension = path.suffix.lower()
            
            if extension == '.json':
                return await self._read_json_file(file_path)
            elif extension == '.csv':
                return await self._read_csv_file(file_path)
            else:
                raise FileError(f"Unsupported file format: {extension}. Supported formats: .json, .csv")
                
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"Failed to read weather data from file {file_path}: {e}")
    
    async def _read_json_file(self, file_path: str) -> List[WeatherData]:
        """Read weather data from JSON file."""
        try:
            content = await self.file_repository.read(file_path)
            import json
            data = json.loads(content)
            
            weather_data_list = []
            
            # Handle different JSON structures
            if isinstance(data, dict):
                # Check if data is wrapped in a structure
                if 'data' in data:
                    data_list = data['data']
                elif 'weather_data' in data:
                    data_list = data['weather_data']
                else:
                    # Assume the dict itself contains the data list
                    data_list = [data]
            elif isinstance(data, list):
                data_list = data
            else:
                raise FileError("Invalid JSON structure. Expected object or array.")
            
            for item in data_list:
                weather_data = self._convert_dict_to_weather_data(item)
                if weather_data:
                    weather_data_list.append(weather_data)
            
            return weather_data_list
            
        except Exception as e:
            raise FileError(f"Failed to read JSON file {file_path}: {e}")
    
    async def _read_csv_file(self, file_path: str) -> List[WeatherData]:
        """Read weather data from CSV file."""
        try:
            content = await self.file_repository.read(file_path)
            # Use pandas to read CSV from content
            import io
            df = pd.read_csv(io.StringIO(content))
            
            weather_data_list = []
            
            for _, row in df.iterrows():
                # Convert row to dict for processing
                item = row.to_dict()
                weather_data = self._convert_dict_to_weather_data(item)
                if weather_data:
                    weather_data_list.append(weather_data)
            
            return weather_data_list
            
        except Exception as e:
            raise FileError(f"Failed to read CSV file {file_path}: {e}")
    
    def _convert_dict_to_weather_data(self, data: Dict[str, Any]) -> Optional[WeatherData]:
        """Convert dictionary to WeatherData entity."""
        try:
            # Parse time field
            time_str = data.get('time') or data.get('date') or data.get('datetime')
            if not time_str:
                return None
            
            # Handle different time formats
            if isinstance(time_str, str):
                # Try common datetime formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        time = datetime.strptime(time_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # Try pandas datetime parsing as fallback
                    try:
                        time = pd.to_datetime(time_str).to_pydatetime()
                    except:
                        return None
            else:
                # Assume it's already a datetime object
                time = time_str
            
            # Extract weather metrics with flexible field names
            temperature_2m_max = self._extract_float_value(data, ['temperature_2m_max', 'temp_max', 'max_temp', 'temperature_max'])
            temperature_2m_min = self._extract_float_value(data, ['temperature_2m_min', 'temp_min', 'min_temp', 'temperature_min'])
            temperature_2m_mean = self._extract_float_value(data, ['temperature_2m_mean', 'temp_mean', 'avg_temp', 'temperature_avg', 'temperature'])
            precipitation_sum = self._extract_float_value(data, ['precipitation_sum', 'precipitation', 'rain', 'rainfall'])
            sunshine_duration = self._extract_float_value(data, ['sunshine_duration', 'sunshine', 'sun_hours'])
            
            return WeatherData(
                time=time,
                temperature_2m_max=temperature_2m_max,
                temperature_2m_min=temperature_2m_min,
                temperature_2m_mean=temperature_2m_mean,
                precipitation_sum=precipitation_sum,
                sunshine_duration=sunshine_duration
            )
            
        except Exception:
            # Return None for invalid records instead of raising exception
            return None
    
    def _extract_float_value(self, data: Dict[str, Any], field_names: List[str]) -> Optional[float]:
        """Extract float value from data using multiple possible field names."""
        for field_name in field_names:
            value = data.get(field_name)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def validate_input_file_format(self, file_path: str) -> bool:
        """Validate if input file format is supported."""
        try:
            from pathlib import Path
            path = Path(file_path)
            extension = path.suffix.lower()
            return extension in ['.json', '.csv']
        except Exception:
            return False
    
    async def get_input_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about the input weather data file."""
        try:
            from pathlib import Path
            path = Path(file_path)
            
            if not self.file_repository.exists(file_path):
                raise FileError(f"File not found: {file_path}")
            
            file_info = {
                'file_path': str(path.absolute()),
                'file_size': path.stat().st_size,
                'file_extension': path.suffix.lower(),
                'is_readable': path.is_file()
            }
            
            # Try to get sample data to determine structure
            try:
                sample_data = await self.read_weather_data_from_file(file_path)
                file_info.update({
                    'record_count': len(sample_data),
                    'has_data': len(sample_data) > 0,
                    'sample_record': sample_data[0] if sample_data else None
                })
            except Exception:
                file_info.update({
                    'record_count': 0,
                    'has_data': False,
                    'sample_record': None
                })
            
            return file_info
            
        except Exception as e:
            raise FileError(f"Failed to get file info for {file_path}: {e}")
    
    # ===== Writing Methods =====
    
    async def write_predictions_to_file(
        self, 
        predictions: List[Forecast], 
        output_path: str,
        format_type: str = 'auto',
        include_metadata: bool = True
    ) -> None:
        """Write predictions to file in specified format."""
        try:
            if not self.validate_output_path(output_path):
                raise FileError(f"Invalid output path: {output_path}")
            
            # Determine format
            if format_type == 'auto':
                from pathlib import Path
                path = Path(output_path)
                format_type = self._determine_output_format_from_extension(path.suffix)
            
            if format_type == 'json':
                await self._write_json_file(predictions, output_path, include_metadata)
            elif format_type == 'csv':
                await self._write_csv_file(predictions, output_path, include_metadata)
            else:
                raise FileError(f"Unsupported output format: {format_type}. Supported formats: json, csv")
                
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"Failed to write predictions to file {output_path}: {e}")
    
    def _determine_output_format_from_extension(self, extension: str) -> str:
        """Determine file format from file extension."""
        extension_map = {
            '.json': 'json',
            '.csv': 'csv'
        }
        
        format_type = extension_map.get(extension.lower())
        if not format_type:
            raise FileError(f"Unsupported file extension: {extension}. Supported extensions: .json, .csv")
        
        return format_type
    
    async def _write_json_file(
        self, 
        predictions: List[Forecast], 
        output_path: str,
        include_metadata: bool
    ) -> None:
        """Write predictions to JSON file."""
        try:
            # Convert forecasts to dictionaries
            predictions_data = []
            for forecast in predictions:
                prediction_dict = {
                    'date': forecast.date.isoformat(),
                    'predicted_value': forecast.predicted_value,
                }
                
                # Add confidence intervals if available
                if forecast.confidence_lower is not None:
                    prediction_dict['confidence_lower'] = forecast.confidence_lower
                if forecast.confidence_upper is not None:
                    prediction_dict['confidence_upper'] = forecast.confidence_upper
                
                predictions_data.append(prediction_dict)
            
            # Create output structure
            output_data = {
                'predictions': predictions_data,
                'model_type': 'ARIMA',
                'prediction_days': len(predictions_data)
            }
            
            # 厳密なIFバリデーション
            try:
                OutputValidator.validate_arima_output(output_data)
            except OutputValidationError as e:
                raise FileError(f"Output validation failed: {e}")
            
            # Add metadata if requested
            if include_metadata:
                output_data['metadata'] = {
                    'generated_at': datetime.now().isoformat(),
                    'model_type': 'ARIMA',
                    'file_format': 'json'
                }
            
            # Write to file
            import json
            json_content = json.dumps(output_data, indent=2, ensure_ascii=False)
            await self.file_repository.write(json_content, output_path)
                
        except Exception as e:
            raise FileError(f"Failed to write JSON file {output_path}: {e}")
    
    async def _write_csv_file(
        self, 
        predictions: List[Forecast], 
        output_path: str,
        include_metadata: bool
    ) -> None:
        """Write predictions to CSV file."""
        try:
            # Convert forecasts to list of dictionaries for pandas
            predictions_data = []
            for forecast in predictions:
                prediction_dict = {
                    'date': forecast.date.isoformat(),
                    'predicted_value': forecast.predicted_value,
                }
                
                # Add confidence intervals if available
                if forecast.confidence_lower is not None:
                    prediction_dict['confidence_lower'] = forecast.confidence_lower
                if forecast.confidence_upper is not None:
                    prediction_dict['confidence_upper'] = forecast.confidence_upper
                
                predictions_data.append(prediction_dict)
            
            # 厳密なIFバリデーション（ARIMA形式）
            output_data = {
                'predictions': predictions_data,
                'model_type': 'ARIMA',
                'prediction_days': len(predictions_data)
            }
            
            try:
                OutputValidator.validate_arima_output(output_data)
            except OutputValidationError as e:
                raise FileError(f"Output validation failed: {e}")
            
            # Create DataFrame and write to CSV
            df = pd.DataFrame(predictions_data)
            csv_content = df.to_csv(index=False, encoding='utf-8')
            await self.file_repository.write(csv_content, output_path)
            
            # Add metadata as comment if requested
            if include_metadata:
                metadata = {
                    'generated_at': datetime.now().isoformat(),
                    'model_type': 'ARIMA',
                    'file_format': 'csv',
                    'total_predictions': len(predictions_data)
                }
                
                # Read current content and prepend metadata
                content = await self.file_repository.read(output_path)
                metadata_header = '\n'.join([f'# {k}: {v}' for k, v in metadata.items()])
                new_content = f"{metadata_header}\n{content}"
                
                await self.file_repository.write(new_content, output_path)
                
        except Exception as e:
            raise FileError(f"Failed to write CSV file {output_path}: {e}")
    
    def validate_output_path(self, output_path: str) -> bool:
        """Validate if output path is writable."""
        try:
            from pathlib import Path
            path = Path(output_path)
            
            # Check if directory exists or can be created
            if not path.parent.exists():
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    return False
            
            # Check if we can write to the directory
            if not path.parent.is_dir():
                return False
            
            # Check extension
            extension = path.suffix.lower()
            if extension not in ['.json', '.csv']:
                return False
            
            return True
        except Exception:
            return False

