"""LLM-based gateway for task schedule generation."""

import os
from pathlib import Path
from typing import List, Dict, Any

from agrr_core.entity.entities.task_schedule_result_entity import TaskScheduleResult
from agrr_core.entity.entities.task_schedule_entity import TaskSchedule
from agrr_core.usecase.gateways.task_schedule_generation_gateway import TaskScheduleGenerationGateway
from agrr_core.adapter.interfaces.clients.llm_client_interface import LLMClientInterface


# Debug mode - set to True for debugging
DEBUG_MODE = os.getenv("AGRRCORE_DEBUG", "false").lower() == "true"

def debug_print(message: str) -> None:
    """Print debug message if debug mode is enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def load_prompt_template(filename: str) -> str:
    """Load prompt template from prompts directory.
    
    Args:
        filename: Name of the prompt file
        
    Returns:
        Content of the prompt file
    """
    import sys
    
    # Check if running as PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)  # type: ignore
        prompt_path = base_path / "prompts" / filename
    else:
        # Running in normal Python environment
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent.parent
        prompt_path = project_root / "prompts" / filename
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")

def extract_prompt_section(content: str, section_name: str) -> str:
    """Extract a specific section from markdown prompt content.
    
    Args:
        content: Full markdown content
        section_name: Name of the section to extract
        
    Returns:
        Extracted section content
    """
    lines = content.split('\n')
    in_section = False
    in_code_block = False
    section_lines = []
    code_block_count = 0
    
    for i, line in enumerate(lines):
        # Check if this is the section we're looking for
        if f"## {section_name}" in line or f"### {section_name}" in line:
            in_section = True
            continue
            
        # If we're in the section
        if in_section:
            # Check if we're entering/exiting a code block
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                code_block_count += 1
                # If this is the opening ``` of the first code block, skip it
                if code_block_count == 1:
                    continue
                # If this is the closing ``` and we're exiting code block, check if section ends
                if not in_code_block:
                    # Check next line to see if it's a new section
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('##'):
                        break
                    continue
                
            # Check if we've reached the next section (only when not in code block)
            if line.startswith('##') and not in_code_block:
                break
                
            # Add line
            section_lines.append(line)
    
    result = '\n'.join(section_lines).strip()
    # Remove trailing markdown code block marker if present
    if result.endswith('```'):
        result = result[:result.rfind('```')].strip()
    
    return result


class TaskScheduleLLMGateway(TaskScheduleGenerationGateway):
    """LLM-based gateway for task schedule generation.
    
    This gateway uses an LLM client to generate task schedules dynamically
    based on crop requirements and available tasks.
    """
    
    def __init__(self, llm_client: LLMClientInterface):
        """Initialize LLM gateway.
        
        Args:
            llm_client: LLM client for generating schedules
        """
        self.llm_client = llm_client
    
    async def generate_task_schedule(
        self,
        crop_name: str,
        variety: str,
        stage_requirements: List[Dict[str, Any]],
        agricultural_tasks: List[Dict[str, Any]]
    ) -> TaskScheduleResult:
        """Generate task schedule using LLM.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            stage_requirements: List of stage requirements
            agricultural_tasks: List of agricultural tasks
            
        Returns:
            Generated TaskScheduleResult
        """
        # Load prompt template
        prompt_content = load_prompt_template("task_schedule_generation.md")
        query_template = extract_prompt_section(prompt_content, "プロンプトテンプレート")
        
        # Replace placeholders
        query = query_template.replace("{作物名}", crop_name).replace("{品種名}", variety)
        
        # Prepare input data
        input_data = {
            "crop_name": crop_name,
            "variety": variety,
            "stage_requirements": stage_requirements,
            "agricultural_tasks": agricultural_tasks
        }
        
        # Combine query with input data
        full_query = f"{query}\n\n### 入力データ\n```json\n{input_data}\n```"
        
        # Define output structure
        structure = {
            "task_schedules": [
                {
                    "task_id": None,
                    "stage_order": None,
                    "gdd_trigger": None,
                    "gdd_tolerance": None,
                    "priority": None,
                    "precipitation_max": None,
                    "wind_speed_max": None,
                    "temperature_min": None,
                    "temperature_max": None,
                    "description": None
                }
            ]
        }
        
        # Generate schedule using LLM
        result = await self.llm_client.struct(full_query, structure, "Generate task schedule based on crop requirements and available tasks.")
        debug_print(f"LLM result: {result['data']}")
        
        # Parse and create TaskSchedule objects
        task_schedules = []
        for schedule_data in result.get("data", {}).get("task_schedules", []):
            task_schedule = TaskSchedule(
                task_id=schedule_data.get("task_id", ""),
                stage_order=int(schedule_data.get("stage_order", 0)),
                gdd_trigger=float(schedule_data.get("gdd_trigger", 0)),
                gdd_tolerance=float(schedule_data.get("gdd_tolerance", 0)),
                priority=int(schedule_data.get("priority", 1)),
                precipitation_max=float(schedule_data.get("precipitation_max", 0)),
                wind_speed_max=float(schedule_data.get("wind_speed_max", 0)),
                temperature_min=schedule_data.get("temperature_min"),
                temperature_max=schedule_data.get("temperature_max"),
                description=schedule_data.get("description", "")
            )
            task_schedules.append(task_schedule)
        
        # Calculate total duration
        total_duration_days = sum(
            task.get("time_per_sqm", 0) * 100  # Assume 100 sqm area
            for task in agricultural_tasks
        ) / 24  # Convert hours to days
        
        # Extract weather dependencies
        weather_dependencies = list(set(
            task.get("weather_dependency", "low")
            for task in agricultural_tasks
        ))
        
        return TaskScheduleResult(
            crop_name=crop_name,
            variety=variety,
            task_schedules=task_schedules,
            total_duration_days=total_duration_days,
            weather_dependencies=weather_dependencies
        )
    
    async def validate_task_schedule(self, task_schedule: TaskScheduleResult) -> bool:
        """Validate generated task schedule.
        
        Args:
            task_schedule: Task schedule to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check basic requirements
        if not task_schedule.crop_name or not task_schedule.variety:
            return False
        
        if not task_schedule.task_schedules:
            return False
        
        # Check task schedules
        for schedule in task_schedule.task_schedules:
            if not schedule.task_id:
                return False
            
            if schedule.stage_order < 1:
                return False
            
            if schedule.gdd_trigger < 0:
                return False
            
            if schedule.gdd_tolerance < 0:
                return False
            
            if schedule.priority < 1:
                return False
        
        return True
