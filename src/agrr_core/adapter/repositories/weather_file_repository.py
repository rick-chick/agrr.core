"""Weather file repository for adapter layer."""

import json
import csv
import pandas as pd
from typing import List, Dict, Any, Union, Optional
from datetime import datetime
from pathlib import Path

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.file_error import FileError


class WeatherFileRepository:
    """Repository for reading weather data from files and writing predictions to files."""
    
    def __init__(self):
        """Initialize weather file repository."""
        pass
    
    # ===== Reading Methods =====
    
    async def read_weather_data_from_file(self, file_path: str) -> List[WeatherData]:
        """Read weather data from JSON or CSV file."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileError(f"File not found: {file_path}")
            
            if not path.is_file():
                raise FileError(f"Path is not a file: {file_path}")
            
            # Determine file format by extension
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
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
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
            
        except json.JSONDecodeError as e:
            raise FileError(f"Invalid JSON format in file {file_path}: {e}")
        except Exception as e:
            raise FileError(f"Failed to read JSON file {file_path}: {e}")
    
    async def _read_csv_file(self, file_path: str) -> List[WeatherData]:
        """Read weather data from CSV file."""
        try:
            # Use pandas to read CSV for better handling of different formats
            df = pd.read_csv(file_path)
            
            weather_data_list = []
            
            for _, row in df.iterrows():
                # Convert row to dict for processing
                item = row.to_dict()
                weather_data = self._convert_dict_to_weather_data(item)
                if weather_data:
                    weather_data_list.append(weather_data)
            
            return weather_data_list
            
        except pd.errors.EmptyDataError:
            raise FileError(f"CSV file is empty: {file_path}")
        except pd.errors.ParserError as e:
            raise FileError(f"Failed to parse CSV file {file_path}: {e}")
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
            path = Path(file_path)
            extension = path.suffix.lower()
            return extension in ['.json', '.csv']
        except Exception:
            return False
    
    async def get_input_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about the input weather data file."""
        try:
            path = Path(file_path)
            
            if not path.exists():
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
            path = Path(output_path)
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine format
            if format_type == 'auto':
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
                'total_predictions': len(predictions_data)
            }
            
            # Add metadata if requested
            if include_metadata:
                output_data['metadata'] = {
                    'generated_at': datetime.now().isoformat(),
                    'model_type': 'ARIMA',
                    'file_format': 'json'
                }
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(output_data, file, indent=2, ensure_ascii=False)
                
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
            
            # Create DataFrame and write to CSV
            df = pd.DataFrame(predictions_data)
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            # Add metadata as comment if requested
            if include_metadata:
                metadata = {
                    'generated_at': datetime.now().isoformat(),
                    'model_type': 'ARIMA',
                    'file_format': 'csv',
                    'total_predictions': len(predictions_data)
                }
                
                # Write metadata as comment at the top of the file
                with open(output_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                metadata_header = '\n'.join([f'# {k}: {v}' for k, v in metadata.items()])
                
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.write(f"{metadata_header}\n{content}")
                
        except Exception as e:
            raise FileError(f"Failed to write CSV file {output_path}: {e}")
    
    
    
    def validate_output_path(self, output_path: str) -> bool:
        """Validate if output path is writable."""
        try:
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
