"""Tests for CropCliCraftController."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from io import StringIO
import json

from agrr_core.adapter.controllers.crop_cli_craft_controller import CropCliCraftController
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway as CropProfileGatewayImpl
from agrr_core.adapter.presenters.crop_profile_craft_presenter import CropProfileCraftPresenter


class TestCropCliCraftController:
    """Test cases for CropCliCraftController."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_gateway = Mock(spec=CropProfileGatewayImpl)
        self.mock_presenter = Mock(spec=CropProfileCraftPresenter)
        
        self.controller = CropCliCraftController(
            gateway=self.mock_gateway,
            presenter=self.mock_presenter
        )
    
    # ===== Argument Parser Tests =====
    
    def test_create_argument_parser(self):
        """Test creating argument parser."""
        parser = self.controller.create_argument_parser()
        
        # Check parser attributes
        assert parser.description == "Crop Profile CLI - Get crop growth profiles using AI"
        
        # Check that required arguments exist
        actions = [action.dest for action in parser._actions]
        assert 'query' in actions
    
    def test_create_argument_parser_with_query(self):
        """Test parser with query argument."""
        parser = self.controller.create_argument_parser()
        
        # Parse with required query argument
        args = parser.parse_args(['--query', 'トマト'])
        
        assert args.query == 'トマト'
    
    # ===== Data Transfer Tests: CLI Args → RequestDTO =====
    
    @pytest.mark.asyncio
    async def test_handle_craft_command_cli_args_to_request_dto(self):
        """Test data transfer from CLI args to RequestDTO."""
        # Mock interactor execute to capture request
        self.controller.interactor.execute = AsyncMock(
            return_value={"success": True, "data": {"crop_name": "tomato"}}
        )
        
        # Mock arguments
        args = Mock()
        args.query = "トマト"
        args.json = True
        
        # Execute
        with patch('sys.stdout', new=StringIO()):
            await self.controller.handle_craft_command(args)
        
        # Verify interactor was called with correct RequestDTO
        self.controller.interactor.execute.assert_called_once()
        call_args = self.controller.interactor.execute.call_args[0][0]
        
        # Verify RequestDTO contains the query
        assert call_args.crop_query == "トマト"
    
    @pytest.mark.asyncio
    async def test_handle_craft_command_japanese_query(self):
        """Test handling Japanese query string."""
        # Mock interactor response
        self.controller.interactor.execute = AsyncMock(
            return_value={
                "success": True,
                "data": {
                    "crop_name": "tomato",
                    "variety": "general",
                    "base_temperature": 10.0,
                    "gdd_requirement": 2000.0,
                    "stages": []
                }
            }
        )
        
        # Mock arguments with Japanese query
        args = Mock()
        args.query = "アイコトマト"
        args.json = True
        
        # Execute
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            await self.controller.handle_craft_command(args)
            output = fake_stdout.getvalue()
        
        # Verify interactor was called
        self.controller.interactor.execute.assert_called_once()
        
        # Verify output is JSON
        result = json.loads(output)
        assert result["success"] is True
        assert result["data"]["crop_name"] == "tomato"
    
    # ===== Data Transfer Tests: Interactor Result → JSON Output =====
    
    @pytest.mark.asyncio
    async def test_handle_craft_command_success_json_output(self):
        """Test data transfer from interactor result to JSON output."""
        # Mock successful interactor response
        mock_result = {
            "success": True,
            "data": {
                "crop_name": "rice",
                "variety": "Koshihikari",
                "base_temperature": 10.0,
                "gdd_requirement": 2400.0,
                "stages": [
                    {
                        "name": "germination",
                        "gdd_requirement": 200.0,
                        "optimal_temp_min": 20.0,
                        "optimal_temp_max": 30.0,
                        "description": "種子発芽期"
                    }
                ]
            }
        }
        
        self.controller.interactor.execute = AsyncMock(return_value=mock_result)
        
        # Mock arguments
        args = Mock()
        args.query = "稲"
        args.json = True
        
        # Execute
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            await self.controller.handle_craft_command(args)
            output = fake_stdout.getvalue()
        
        # Verify output is valid JSON
        result = json.loads(output)
        
        # Verify all data fields are preserved
        assert result["success"] is True
        assert result["data"]["crop_name"] == "rice"
        assert result["data"]["variety"] == "Koshihikari"
        assert result["data"]["base_temperature"] == 10.0
        assert result["data"]["gdd_requirement"] == 2400.0
        assert len(result["data"]["stages"]) == 1
        assert result["data"]["stages"][0]["name"] == "germination"
        assert result["data"]["stages"][0]["description"] == "種子発芽期"
    
    @pytest.mark.asyncio
    async def test_handle_craft_command_error_json_output(self):
        """Test data transfer for error response to JSON output."""
        # Mock error interactor response
        mock_error = {
            "success": False,
            "error": "Failed to craft crop requirement"
        }
        
        self.controller.interactor.execute = AsyncMock(return_value=mock_error)
        
        # Mock arguments
        args = Mock()
        args.query = "invalid-crop"
        args.json = True
        
        # Execute
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            await self.controller.handle_craft_command(args)
            output = fake_stdout.getvalue()
        
        # Verify error output is valid JSON
        result = json.loads(output)
        
        assert result["success"] is False
        assert "error" in result
        assert "Failed to craft crop requirement" in result["error"]
    
    # ===== Data Integrity Tests =====
    
    @pytest.mark.asyncio
    async def test_ensure_ascii_false_preserves_unicode(self):
        """Test that ensure_ascii=False preserves Japanese characters."""
        # Mock interactor response with Japanese description
        mock_result = {
            "success": True,
            "data": {
                "crop_name": "tomato",
                "stages": [
                    {
                        "name": "vegetative",
                        "description": "栄養成長期"
                    }
                ]
            }
        }
        
        self.controller.interactor.execute = AsyncMock(return_value=mock_result)
        
        # Mock arguments
        args = Mock()
        args.query = "トマト"
        args.json = True
        
        # Execute
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            await self.controller.handle_craft_command(args)
            output = fake_stdout.getvalue()
        
        # Verify Japanese characters are preserved (not escaped)
        assert "栄養成長期" in output
        # Should not be escaped like "\u6804\u990a\u6210\u9577\u671f"
        assert "\\u" not in output
    
    @pytest.mark.asyncio
    async def test_numeric_precision_preserved(self):
        """Test that numeric values maintain precision through data transfer."""
        # Mock interactor response with precise values
        mock_result = {
            "success": True,
            "data": {
                "crop_name": "tomato",
                "base_temperature": 10.5,
                "gdd_requirement": 2400.75,
                "stages": [
                    {
                        "name": "germination",
                        "gdd_requirement": 150.25,
                        "optimal_temp_min": 20.3,
                        "optimal_temp_max": 30.7
                    }
                ]
            }
        }
        
        self.controller.interactor.execute = AsyncMock(return_value=mock_result)
        
        # Mock arguments
        args = Mock()
        args.query = "トマト"
        args.json = True
        
        # Execute
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            await self.controller.handle_craft_command(args)
            output = fake_stdout.getvalue()
        
        # Verify numeric precision is preserved
        result = json.loads(output)
        assert result["data"]["base_temperature"] == 10.5
        assert result["data"]["gdd_requirement"] == 2400.75
        assert result["data"]["stages"][0]["gdd_requirement"] == 150.25
        assert result["data"]["stages"][0]["optimal_temp_min"] == 20.3
        assert result["data"]["stages"][0]["optimal_temp_max"] == 30.7
    
    # ===== Run Method Tests =====
    
    @pytest.mark.asyncio
    async def test_run_no_query(self):
        """Test run method with no query argument provided."""
        # Should raise SystemExit because --query is required
        with pytest.raises(SystemExit):
            await self.controller.run([])
    
    @pytest.mark.asyncio
    async def test_run_with_query(self):
        """Test run method with query argument."""
        self.controller.interactor.execute = AsyncMock(
            return_value={"crop": {"crop_id": "tomato", "name": "Tomato"}, "stage_requirements": []}
        )
        
        args = ['--query', 'トマト']
        
        with patch('sys.stdout', new=StringIO()):
            await self.controller.run(args)
        
        self.controller.interactor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_with_invalid_argument(self):
        """Test run method with invalid argument."""
        # Invalid argument should raise SystemExit
        with pytest.raises(SystemExit):
            await self.controller.run(['--invalid-arg'])
    
    # ===== Integration Tests with Gateway and Presenter =====
    
    def test_controller_has_required_dependencies(self):
        """Test that controller has all required dependencies injected."""
        assert self.controller.gateway is not None
        assert self.controller.presenter is not None
        assert self.controller.interactor is not None
    
    def test_interactor_instantiated_in_controller(self):
        """Test that interactor is instantiated inside controller."""
        from agrr_core.usecase.interactors.crop_profile_craft_interactor import (
            CropProfileCraftInteractor,
        )
        
        # Interactor should be an instance created by controller
        assert isinstance(self.controller.interactor, CropProfileCraftInteractor)
        
        # Interactor should have the same gateway and presenter
        assert self.controller.interactor.gateway == self.controller.gateway
        assert self.controller.interactor.presenter == self.controller.presenter
    
    # ===== Edge Cases =====
    
    @pytest.mark.asyncio
    async def test_handle_craft_command_empty_stages(self):
        """Test handling crop requirement with empty stages list."""
        mock_result = {
            "success": True,
            "data": {
                "crop_name": "unknown",
                "variety": "general",
                "base_temperature": 10.0,
                "gdd_requirement": 1000.0,
                "stages": []  # Empty stages
            }
        }
        
        self.controller.interactor.execute = AsyncMock(return_value=mock_result)
        
        args = Mock()
        args.query = "unknown-crop"
        args.json = True
        
        # Should not raise error even with empty stages
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            await self.controller.handle_craft_command(args)
            output = fake_stdout.getvalue()
        
        result = json.loads(output)
        assert result["success"] is True
        assert result["data"]["stages"] == []
    
    @pytest.mark.asyncio
    async def test_handle_craft_command_special_characters(self):
        """Test handling query with special characters."""
        mock_result = {
            "success": True,
            "data": {"crop_name": "special"}
        }
        
        self.controller.interactor.execute = AsyncMock(return_value=mock_result)
        
        args = Mock()
        args.query = "作物名/品種①"  # Special characters
        args.json = True
        
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            await self.controller.handle_craft_command(args)
            output = fake_stdout.getvalue()
        
        # Should handle special characters without error
        result = json.loads(output)
        assert result["success"] is True
        
        # Verify interactor received the query correctly
        call_args = self.controller.interactor.execute.call_args[0][0]
        assert call_args.crop_query == "作物名/品種①"

