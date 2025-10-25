"""Tests for TaskScheduleGenerationInteractor."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agrr_core.usecase.interactors.task_schedule_generation_interactor import TaskScheduleGenerationInteractor
from agrr_core.usecase.dto.task_schedule_generation_request_dto import TaskScheduleGenerationRequestDTO
from agrr_core.entity.entities.task_schedule_result_entity import TaskScheduleResult
from agrr_core.entity.entities.task_schedule_entity import TaskSchedule


class TestTaskScheduleGenerationInteractor:
    """Test cases for TaskScheduleGenerationInteractor."""
    
    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = AsyncMock()
        return gateway
    
    @pytest.fixture
    def interactor(self, mock_gateway):
        """Create interactor with mock gateway."""
        return TaskScheduleGenerationInteractor(mock_gateway)
    
    @pytest.fixture
    def valid_request(self):
        """Create valid request DTO."""
        return TaskScheduleGenerationRequestDTO(
            crop_name="トマト",
            variety="桃太郎",
            stage_requirements=[
                {
                    "stage": {"name": "育苗期", "order": 1},
                    "temperature": {"base_temperature": 10.0}
                }
            ],
            agricultural_tasks=[
                {
                    "task_id": "soil_preparation",
                    "task_name": "土壌準備",
                    "description": "畑の耕起、施肥、マルチング",
                    "time_per_sqm": 0.5,
                    "weather_dependency": "low",
                    "precipitation_max": 0.5,
                    "wind_speed_max": 10.0
                }
            ]
        )
    
    @pytest.fixture
    def mock_result(self):
        """Create mock result."""
        return TaskScheduleResult(
            crop_name="トマト",
            variety="桃太郎",
            task_schedules=[
                TaskSchedule(
                    task_id="soil_preparation",
                    stage_order=1,
                    gdd_trigger=0,
                    gdd_tolerance=0,
                    priority=1,
                    precipitation_max=0.5,
                    wind_speed_max=10.0,
                    description="栽培開始前の土壌準備"
                )
            ],
            total_duration_days=2.0,
            weather_dependencies=["low"]
        )
    
    @pytest.mark.asyncio
    async def test_execute_success(self, interactor, mock_gateway, valid_request, mock_result):
        """Test successful execution."""
        # Setup mock
        mock_gateway.generate_task_schedule.return_value = mock_result
        mock_gateway.validate_task_schedule.return_value = True
        
        # Execute
        result = await interactor.execute(valid_request)
        
        # Verify
        assert result == mock_result
        mock_gateway.generate_task_schedule.assert_called_once_with(
            crop_name="トマト",
            variety="桃太郎",
            stage_requirements=valid_request.stage_requirements,
            agricultural_tasks=valid_request.agricultural_tasks
        )
        mock_gateway.validate_task_schedule.assert_called_once_with(mock_result)
    
    @pytest.mark.asyncio
    async def test_execute_invalid_request(self, interactor, mock_gateway):
        """Test execution with invalid request."""
        # Create invalid request
        invalid_request = TaskScheduleGenerationRequestDTO(
            crop_name="",  # Empty crop name
            variety="桃太郎",
            stage_requirements=[],
            agricultural_tasks=[]
        )
        
        # Execute and expect ValueError
        with pytest.raises(ValueError, match="Invalid request data"):
            await interactor.execute(invalid_request)
    
    @pytest.mark.asyncio
    async def test_execute_generation_failure(self, interactor, mock_gateway, valid_request):
        """Test execution with generation failure."""
        # Setup mock to raise exception
        mock_gateway.generate_task_schedule.side_effect = Exception("LLM error")
        
        # Execute and expect RuntimeError
        with pytest.raises(RuntimeError, match="Task schedule generation failed"):
            await interactor.execute(valid_request)
    
    @pytest.mark.asyncio
    async def test_execute_validation_failure(self, interactor, mock_gateway, valid_request, mock_result):
        """Test execution with validation failure."""
        # Setup mock
        mock_gateway.generate_task_schedule.return_value = mock_result
        mock_gateway.validate_task_schedule.return_value = False
        
        # Execute and expect RuntimeError
        with pytest.raises(RuntimeError, match="Generated task schedule is invalid"):
            await interactor.execute(valid_request)
    
    @pytest.mark.asyncio
    async def test_generate_for_crop_success(self, interactor, mock_gateway, mock_result):
        """Test generate_for_crop convenience method."""
        # Setup mock
        mock_gateway.generate_task_schedule.return_value = mock_result
        mock_gateway.validate_task_schedule.return_value = True
        
        # Execute
        result = await interactor.generate_for_crop(
            crop_name="トマト",
            variety="桃太郎",
            stage_requirements=[{"stage": {"name": "育苗期", "order": 1}}],
            agricultural_tasks=[{"task_id": "soil_preparation"}]
        )
        
        # Verify
        assert result == mock_result
        mock_gateway.generate_task_schedule.assert_called_once()
        mock_gateway.validate_task_schedule.assert_called_once()
