"""CLI controller for task schedule generation."""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from agrr_core.usecase.interactors.task_schedule_generation_interactor import TaskScheduleGenerationInteractor
from agrr_core.usecase.dto.task_schedule_generation_request_dto import TaskScheduleGenerationRequestDTO

class TaskScheduleGenerationCLIController:
    """CLI controller for task schedule generation.
    
    This controller handles command-line interface for task schedule generation.
    """
    
    def __init__(self, interactor: TaskScheduleGenerationInteractor):
        """Initialize controller.
        
        Args:
            interactor: Task schedule generation interactor
        """
        self.interactor = interactor
    
    def generate_schedule(
        self,
        crop_name: str,
        variety: str,
        stage_requirements_file: str,
        agricultural_tasks_file: str,
        output_file: str = None
    ) -> None:
        """Generate task schedule from files.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            stage_requirements_file: Path to stage requirements JSON file
            agricultural_tasks_file: Path to agricultural tasks JSON file
            output_file: Path to output file (optional)
        """
        try:
            # Load stage requirements
            stage_requirements = self._load_json_file(stage_requirements_file)
            
            # Load agricultural tasks
            agricultural_tasks = self._load_json_file(agricultural_tasks_file)
            
            # Create request
            request = TaskScheduleGenerationRequestDTO(
                crop_name=crop_name,
                variety=variety,
                stage_requirements=stage_requirements,
                agricultural_tasks=agricultural_tasks
            )
            
            # Generate task schedule
            result = self.interactor.execute(request)
            
            # Format and output result
            output_data = self._format_result(result)
            
            if output_file:
                self._save_to_file(output_data, output_file)
                print(f"Task schedule saved to {output_file}")
            else:
                self._print_result(output_data)
                
        except Exception as e:
            print(f"Error generating task schedule: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Loaded JSON data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {file_path} - {str(e)}")
    
    def _format_result(self, result) -> Dict[str, Any]:
        """Format result for output.
        
        Args:
            result: Task schedule result
            
        Returns:
            Formatted result data
        """
        return {
            "crop_name": result.crop_name,
            "variety": result.variety,
            "total_duration_days": result.total_duration_days,
            "weather_dependencies": result.weather_dependencies,
            "task_schedules": [
                {
                    "task_id": schedule.task_id,
                    "stage_order": schedule.stage_order,
                    "gdd_trigger": schedule.gdd_trigger,
                    "gdd_tolerance": schedule.gdd_tolerance,
                    "priority": schedule.priority,
                    "precipitation_max": schedule.precipitation_max,
                    "wind_speed_max": schedule.wind_speed_max,
                    "temperature_min": schedule.temperature_min,
                    "temperature_max": schedule.temperature_max,
                    "description": schedule.description
                }
                for schedule in result.task_schedules
            ]
        }
    
    def _save_to_file(self, data: Dict[str, Any], file_path: str) -> None:
        """Save data to file.
        
        Args:
            data: Data to save
            file_path: Path to output file
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _print_result(self, data: Dict[str, Any]) -> None:
        """Print result to console.
        
        Args:
            data: Result data to print
        """
        print("=" * 80)
        print("TASK SCHEDULE GENERATION RESULT")
        print("=" * 80)
        print(f"Crop: {data['crop_name']}")
        print(f"Variety: {data['variety']}")
        print(f"Total Duration: {data['total_duration_days']:.1f} days")
        print(f"Weather Dependencies: {', '.join(data['weather_dependencies'])}")
        print()
        
        print("TASK SCHEDULES:")
        print("-" * 80)
        for schedule in data['task_schedules']:
            print(f"Task ID: {schedule['task_id']}")
            print(f"Stage Order: {schedule['stage_order']}")
            print(f"GDD Trigger: {schedule['gdd_trigger']}")
            print(f"GDD Tolerance: {schedule['gdd_tolerance']}")
            print(f"Priority: {schedule['priority']}")
            print(f"Precipitation Max: {schedule['precipitation_max']} mm")
            print(f"Wind Speed Max: {schedule['wind_speed_max']} m/s")
            if schedule['temperature_min']:
                print(f"Temperature Min: {schedule['temperature_min']} °C")
            if schedule['temperature_max']:
                print(f"Temperature Max: {schedule['temperature_max']} °C")
            print(f"Description: {schedule['description']}")
            print("-" * 80)
