"""Tests for WeatherFileRepository."""

import pytest
import json
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open

from agrr_core.adapter.repositories.weather_file_repository import WeatherFileRepository
from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.file_error import FileError


class TestWeatherFileRepository:
    """Test cases for WeatherFileRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock file repository with proper sync/async method handling
        from unittest.mock import MagicMock, AsyncMock
        self.mock_file_repository = MagicMock()
        # Configure synchronous methods
        self.mock_file_repository.exists.return_value = True
        # Configure asynchronous methods
        self.mock_file_repository.read = AsyncMock(return_value='{"data": [{"time": "2024-01-01", "temperature_2m_max": 25.0}]}')
        self.mock_file_repository.write = AsyncMock(return_value=None)
        self.mock_file_repository.delete = AsyncMock(return_value=None)
        self.repository = WeatherFileRepository(self.mock_file_repository)
    
    # ===== Input Validation Tests =====
    
    def test_validate_input_file_format_json(self):
        """Test validating JSON file format."""
        assert self.repository.validate_input_file_format("test.json") is True
        assert self.repository.validate_input_file_format("test.JSON") is True
    
    def test_validate_input_file_format_csv(self):
        """Test validating CSV file format."""
        assert self.repository.validate_input_file_format("test.csv") is True
        assert self.repository.validate_input_file_format("test.CSV") is True
    
    def test_validate_input_file_format_invalid(self):
        """Test validating invalid file format."""
        assert self.repository.validate_input_file_format("test.txt") is False
        assert self.repository.validate_input_file_format("test") is False
    
    def test_validate_output_path_valid(self):
        """Test validating valid output path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "output.json")
            assert self.repository.validate_output_path(output_path) is True
    
    def test_validate_output_path_invalid_extension(self):
        """Test validating invalid output path extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "output.xyz")
            # .xyz should be invalid for output
            assert self.repository.validate_output_path(output_path) is False
    
    # ===== JSON Reading Tests =====
    
    @pytest.mark.asyncio
    async def test_read_json_file_simple_array(self):
        """Test reading simple JSON array."""
        json_data = [
            {
                "time": "2024-01-01",
                "temperature_2m_max": 25.0,
                "temperature_2m_min": 15.0,
                "temperature_2m_mean": 20.0,
                "precipitation_sum": 2.0,
                "sunshine_duration": 28800
            },
            {
                "time": "2024-01-02", 
                "temperature_2m_max": 26.0,
                "temperature_2m_min": 16.0,
                "temperature_2m_mean": 21.0,
                "precipitation_sum": 0.0,
                "sunshine_duration": 32400
            }
        ]
        
        # Mock file repository to return JSON data
        self.mock_file_repository.read.return_value = json.dumps(json_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            temp_file = f.name
        
        try:
            result = await self.repository._read_json_file(temp_file)
            
            assert len(result) == 2
            assert isinstance(result[0], WeatherData)
            assert result[0].time == datetime(2024, 1, 1)
            assert result[0].temperature_2m_max == 25.0
            assert result[0].temperature_2m_mean == 20.0
            assert result[0].precipitation_sum == 2.0
            assert result[0].sunshine_duration == 28800
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_read_json_file_wrapped_data(self):
        """Test reading JSON with wrapped data structure."""
        json_data = {
            "data": [
                {
                    "time": "2024-01-01",
                    "temperature_2m_max": 25.0,
                    "temperature_2m_min": 15.0,
                    "temperature_2m_mean": 20.0,
                    "precipitation_sum": 2.0,
                    "sunshine_duration": 28800
                }
            ]
        }
        
        # Mock file repository to return JSON data
        self.mock_file_repository.read.return_value = json.dumps(json_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            temp_file = f.name
        
        try:
            result = await self.repository._read_json_file(temp_file)
            
            assert len(result) == 1
            assert result[0].temperature_2m_max == 25.0
            assert result[0].temperature_2m_mean == 20.0
        finally:
            os.unlink(temp_file)
    
    # ===== CSV Reading Tests =====
    
    @pytest.mark.asyncio
    async def test_read_csv_file(self):
        """Test reading CSV file."""
        csv_data = "time,temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,sunshine_duration\n2024-01-01,25.0,15.0,20.0,2.0,28800\n2024-01-02,26.0,16.0,21.0,0.0,32400"
        
        # Mock file repository to return CSV data
        self.mock_file_repository.read.return_value = csv_data
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_file = f.name
        
        try:
            result = await self.repository._read_csv_file(temp_file)
            
            assert len(result) == 2
            assert isinstance(result[0], WeatherData)
            assert result[0].temperature_2m_max == 25.0
            assert result[0].temperature_2m_mean == 20.0
            assert result[0].precipitation_sum == 2.0
        finally:
            os.unlink(temp_file)
    
    # ===== Data Conversion Tests =====
    
    def test_convert_dict_to_weather_data_complete(self):
        """Test converting complete dictionary to WeatherData."""
        data = {
            "time": "2024-01-01",
            "temperature_2m_max": 20.0,
            "temperature_2m_min": 10.0,
            "temperature_2m_mean": 15.0,
            "precipitation_sum": 1.5,
            "sunshine_duration": 36000
        }
        
        result = self.repository._convert_dict_to_weather_data(data)
        
        assert result is not None
        assert isinstance(result, WeatherData)
        assert result.time == datetime(2024, 1, 1)
        assert result.temperature_2m_max == 20.0
        assert result.temperature_2m_min == 10.0
        assert result.temperature_2m_mean == 15.0
        assert result.precipitation_sum == 1.5
        assert result.sunshine_duration == 36000
    
    def test_convert_dict_to_weather_data_minimal(self):
        """Test converting minimal dictionary to WeatherData."""
        data = {
            "time": "2024-01-01",
            "temperature_2m_mean": 15.0
        }
        
        result = self.repository._convert_dict_to_weather_data(data)
        
        assert result is not None
        assert result.temperature_2m_mean == 15.0
        assert result.temperature_2m_max is None
        assert result.temperature_2m_min is None
        assert result.precipitation_sum is None
        assert result.sunshine_duration is None
    
    def test_convert_dict_to_weather_data_no_time(self):
        """Test converting dictionary without time field."""
        data = {
            "temperature_2m_mean": 15.0
        }
        
        result = self.repository._convert_dict_to_weather_data(data)
        
        assert result is None
    
    def test_extract_float_value_success(self):
        """Test extracting float value with multiple field names."""
        data = {
            "temperature": 15.5,
            "temp_avg": 16.0
        }
        
        result = self.repository._extract_float_value(data, ["temperature_2m_mean", "temperature", "temp_avg"])
        
        assert result == 15.5
    
    def test_extract_float_value_not_found(self):
        """Test extracting float value when field not found."""
        data = {"other_field": "value"}
        
        result = self.repository._extract_float_value(data, ["temperature"])
        
        assert result is None
    
    # ===== Output Writing Tests =====
    
    @pytest.mark.asyncio
    async def test_write_json_file(self):
        """Test writing predictions to JSON file."""
        predictions = [
            Forecast(
                date=datetime(2024, 2, 1),
                predicted_value=20.0,
                confidence_lower=18.0,
                confidence_upper=22.0
            ),
            Forecast(
                date=datetime(2024, 2, 2),
                predicted_value=21.0
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        # Mock the file repository write method to capture what would be written
        written_content = None
        async def mock_write(content, file_path):
            nonlocal written_content
            written_content = content
            return None
        
        self.mock_file_repository.write.side_effect = mock_write
        
        try:
            await self.repository._write_json_file(predictions, temp_file, include_metadata=True)
            
            # Verify the mock was called (may be called multiple times for data and metadata)
            assert self.mock_file_repository.write.call_count >= 1
            
            # Parse the written content
            assert written_content is not None
            result = json.loads(written_content)
            
            assert "predictions" in result
            assert "total_predictions" in result
            assert "metadata" in result
            assert result["total_predictions"] == 2
            assert len(result["predictions"]) == 2
            assert result["predictions"][0]["predicted_value"] == 20.0
            assert result["predictions"][0]["confidence_lower"] == 18.0
            assert result["predictions"][0]["confidence_upper"] == 22.0
        finally:
            os.unlink(temp_file)
    
    
    # ===== Error Handling Tests =====
    
    @pytest.mark.asyncio
    async def test_read_weather_data_from_file_not_found(self):
        """Test reading weather data from non-existent file."""
        # Mock file repository to return False for exists (synchronous call)
        from unittest.mock import Mock
        self.mock_file_repository.exists = Mock(return_value=False)
        
        with pytest.raises(FileError, match="File not found"):
            await self.repository.read_weather_data_from_file("nonexistent.json")
    
    @pytest.mark.asyncio
    async def test_read_weather_data_from_file_invalid_format(self):
        """Test reading weather data from invalid file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_file = f.name
        
        try:
            with pytest.raises(FileError, match="Unsupported file format"):
                await self.repository.read_weather_data_from_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_write_predictions_to_file_invalid_format(self):
        """Test writing predictions to invalid file format."""
        predictions = [Forecast(date=datetime.now(), predicted_value=20.0)]
        
        with pytest.raises(FileError, match="Invalid output path"):
            await self.repository.write_predictions_to_file(predictions, "output.xyz", "xyz")
    
    # ===== Integration Tests =====
    
    @pytest.mark.asyncio
    async def test_read_and_write_integration(self):
        """Test reading weather data and writing predictions integration."""
        # Create test JSON file
        json_data = [
            {
                "time": "2024-01-01",
                "temperature_2m_mean": 15.5,
                "precipitation_sum": 2.0
            },
            {
                "time": "2024-01-02",
                "temperature_2m_mean": 16.0,
                "precipitation_sum": 0.0
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            input_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        # Mock file repository to return JSON data
        self.mock_file_repository.read.return_value = json.dumps(json_data)
        
        try:
            # Read weather data
            weather_data = await self.repository.read_weather_data_from_file(input_file)
            assert len(weather_data) == 2
            
            # Create mock predictions
            predictions = [
                Forecast(date=datetime(2024, 2, 1), predicted_value=17.0),
                Forecast(date=datetime(2024, 2, 2), predicted_value=18.0)
            ]
            
            # Mock the file repository write method to capture what would be written
            written_contents = []
            async def mock_write(content, file_path):
                written_contents.append(content)
                return None
            
            self.mock_file_repository.write.side_effect = mock_write
            
            # Write predictions
            await self.repository.write_predictions_to_file(predictions, output_file, include_metadata=True)
            
            # Verify output (check the written content)
            assert len(written_contents) >= 1
            result = json.loads(written_contents[0])  # First call should be the main data
            
            assert result["total_predictions"] == 2
            assert len(result["predictions"]) == 2
        finally:
            os.unlink(input_file)
            os.unlink(output_file)
    
    # ===== Additional Coverage Tests =====
    
    def test_validate_input_file_format_not_a_file(self):
        """Test validating path that is not a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory instead of file
            dir_path = os.path.join(temp_dir, "not_a_file")
            os.makedirs(dir_path)
            assert self.repository.validate_input_file_format(dir_path) is False
    
    @pytest.mark.asyncio
    async def test_read_weather_data_from_file_not_a_file(self):
        """Test reading from path that is not a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = os.path.join(temp_dir, "not_a_file")
            os.makedirs(dir_path)
            
        with pytest.raises(FileError, match="Unsupported file format"):
            await self.repository.read_weather_data_from_file(dir_path)
    
    @pytest.mark.asyncio
    async def test_read_weather_data_from_file_unsupported_format(self):
        """Test reading from unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name
            f.write("some text data")
        
        try:
            with pytest.raises(FileError, match="Unsupported file format: \\.txt"):
                await self.repository.read_weather_data_from_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_read_json_file_with_data_wrapper(self):
        """Test reading JSON with 'data' wrapper."""
        json_data = {
            "data": [
                {
                    "time": "2024-01-01T00:00:00",
                    "temperature_2m_mean": 15.0,
                    "precipitation_sum": 2.5,
                    "sunshine_duration": 8.0
                }
            ]
        }
        
        # Mock file repository to return JSON data
        self.mock_file_repository.read.return_value = json.dumps(json_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            result = await self.repository._read_json_file(temp_file)
            assert len(result) == 1
            assert result[0].temperature_2m_mean == 15.0
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_read_json_file_with_weather_data_wrapper(self):
        """Test reading JSON with 'weather_data' wrapper."""
        json_data = {
            "weather_data": [
                {
                    "time": "2024-01-01T00:00:00",
                    "temperature_2m_mean": 20.0,
                    "precipitation_sum": 0.0,
                    "sunshine_duration": 12.0
                }
            ]
        }
        
        # Mock file repository to return JSON data
        self.mock_file_repository.read.return_value = json.dumps(json_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            result = await self.repository._read_json_file(temp_file)
            assert len(result) == 1
            assert result[0].temperature_2m_mean == 20.0
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_read_json_file_invalid_structure(self):
        """Test reading JSON with invalid structure."""
        # Mock file repository to return invalid JSON
        self.mock_file_repository.read.return_value = "invalid json structure"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            with pytest.raises(FileError, match="Failed to read JSON file"):
                await self.repository._read_json_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_read_csv_file_success(self):
        """Test successful CSV file reading."""
        csv_data = "time,temperature_2m_mean,precipitation_sum,sunshine_duration\n2024-01-01T00:00:00,18.5,1.2,6.5\n2024-01-02T00:00:00,19.0,0.8,7.0"
        
        # Mock file repository to return CSV data
        self.mock_file_repository.read.return_value = csv_data
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            result = await self.repository._read_csv_file(temp_file)
            assert len(result) == 2
            assert result[0].temperature_2m_mean == 18.5
            assert result[1].temperature_2m_mean == 19.0
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_convert_dict_to_weather_data_csv_format(self):
        """Test converting CSV data to WeatherData."""
        csv_data = {
            "time": "2024-01-01T00:00:00",
            "temperature_2m_mean": "22.3",
            "precipitation_sum": "3.1",
            "sunshine_duration": "9.5"
        }
        
        result = self.repository._convert_dict_to_weather_data(csv_data)
        
        assert result is not None
        assert result.temperature_2m_mean == 22.3
        assert result.precipitation_sum == 3.1
        assert result.sunshine_duration == 9.5
    
    @pytest.mark.asyncio
    async def test_get_input_file_info_success(self):
        """Test getting file information."""
        json_data = [
            {
                "time": "2024-01-01T00:00:00",
                "temperature_2m_mean": 15.0,
                "precipitation_sum": 2.5,
                "sunshine_duration": 8.0
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
            json.dump(json_data, f)
        
        try:
            result = await self.repository.get_input_file_info(temp_file)
            
            assert result["file_path"] == str(Path(temp_file).absolute())
            assert result["file_size"] > 0
            assert result["file_extension"] == ".json"
            assert result["is_readable"] is True
            assert result["record_count"] == 1
            assert result["has_data"] is True
            assert result["sample_record"] is not None
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_get_input_file_info_not_found(self):
        """Test getting file information for non-existent file."""
        # Mock file repository to return False for exists (synchronous call)
        from unittest.mock import Mock
        self.mock_file_repository.exists = Mock(return_value=False)
        
        with pytest.raises(FileError, match="Failed to get file info"):
            await self.repository.get_input_file_info("/nonexistent/file.json")
    
    @pytest.mark.asyncio
    async def test_write_csv_file_success(self):
        """Test writing predictions to CSV file."""
        predictions = [
            Forecast(
                date=datetime(2024, 2, 1),
                predicted_value=25.0,
                confidence_lower=23.0,
                confidence_upper=27.0
            ),
            Forecast(
                date=datetime(2024, 2, 2),
                predicted_value=26.0,
                confidence_lower=24.0,
                confidence_upper=28.0
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        # Mock the file repository write method to capture what would be written
        written_contents = []
        async def mock_write(content, file_path):
            written_contents.append(content)
            return None
        
        self.mock_file_repository.write.side_effect = mock_write
        
        try:
            await self.repository._write_csv_file(predictions, temp_file, include_metadata=True)
            
            # Verify the mock was called (may be called multiple times for data and metadata)
            assert self.mock_file_repository.write.call_count >= 1
            
            # Parse the written content (first call should be CSV data)
            assert len(written_contents) >= 1
            csv_content = written_contents[0]  # First call is CSV data
            
            assert "date,predicted_value,confidence_lower,confidence_upper" in csv_content
            assert "2024-02-01T00:00:00,25.0,23.0,27.0" in csv_content
            assert "2024-02-02T00:00:00,26.0,24.0,28.0" in csv_content
        finally:
            os.unlink(temp_file)
    
    def test_determine_output_format_from_extension_json(self):
        """Test determining output format from .json extension."""
        result = self.repository._determine_output_format_from_extension(".json")
        assert result == "json"
    
    def test_determine_output_format_from_extension_csv(self):
        """Test determining output format from .csv extension."""
        result = self.repository._determine_output_format_from_extension(".csv")
        assert result == "csv"
    
    def test_determine_output_format_from_extension_invalid(self):
        """Test determining output format from invalid extension."""
        with pytest.raises(FileError, match="Unsupported file extension"):
            self.repository._determine_output_format_from_extension(".txt")
    
    @pytest.mark.asyncio
    async def test_write_predictions_to_file_csv_format(self):
        """Test writing predictions to file with CSV format."""
        predictions = [
            Forecast(
                date=datetime(2024, 2, 1),
                predicted_value=30.0,
                confidence_lower=28.0,
                confidence_upper=32.0
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        # Mock the file repository write method to capture what would be written
        written_contents = []
        async def mock_write(content, file_path):
            written_contents.append(content)
            return None
        
        self.mock_file_repository.write.side_effect = mock_write
        
        try:
            await self.repository.write_predictions_to_file(
                predictions, 
                temp_file, 
                format_type='csv',
                include_metadata=True
            )
            
            # Verify the mock was called (may be called multiple times for data and metadata)
            assert self.mock_file_repository.write.call_count >= 1
            
            # Parse the written content (first call should be CSV data)
            assert len(written_contents) >= 1
            csv_content = written_contents[0]  # First call is CSV data
            
            assert "date,predicted_value,confidence_lower,confidence_upper" in csv_content
            assert "2024-02-01T00:00:00,30.0,28.0,32.0" in csv_content
        finally:
            os.unlink(temp_file)
