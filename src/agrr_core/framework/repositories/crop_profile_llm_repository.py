"""LLM-based implementation for crop profile generation.

This repository uses LLM client to generate crop profiles dynamically.
It encapsulates all crop-specific prompts and data transformations.
"""

import os
from pathlib import Path
from typing import Dict, Any

from agrr_core.entity import (
    Crop,
    GrowthStage,
    TemperatureProfile,
    SunshineProfile,
    ThermalRequirement,
    StageRequirement,
)
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.adapter.interfaces.llm_client import LLMClient


# Debug mode - set to True for debugging
DEBUG_MODE = os.getenv("AGRRCORE_DEBUG", "false").lower() == "true"

def debug_print(message: str) -> None:
    """Print debug message if debug mode is enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def load_prompt_template(filename: str) -> str:
    """Load prompt template from prompts directory.
    
    Args:
        filename: Name of the prompt file (e.g., 'stage2_growth_stages_research.md')
        
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
        # Get the project root (assuming this file is in src/agrr_core/adapter/repositories/)
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
        section_name: Name of the section to extract (e.g., 'プロンプトテンプレート', '注意事項')
        
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


class CropProfileLLMRepository:
    """LLM-based repository for crop profile generation.
    
    Uses LLM client's generic struct() method to generate crop profiles.
    Encapsulates all crop-specific prompts and data transformations.
    """
    
    def __init__(self, llm_client: LLMClient):
        """Initialize LLM repository.
        
        Args:
            llm_client: LLM client for generating requirements (required)
        """
        self.llm_client = llm_client
    
    async def extract_crop_variety(self, crop_query: str) -> Dict[str, Any]:
        """Step 1: Extract crop name and variety from user input.
        
        Args:
            crop_query: User input containing crop and variety information
            
        Returns:
            Dict containing crop_name and variety
        """
        structure = {
            "crop_name": None,
            "variety": None
        }
        
        instruction = """
        Extract crop name and variety from the user input.
        Return JSON with crop_name and variety fields.
        If variety is not specified, use "default" as variety.
        """
        
        result = await self.llm_client.struct(crop_query, structure, instruction)
        debug_print(f"Step 1 result: {result['data']}")
        return result.get("data", {})

    async def define_growth_stages(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Step 2: Define growth stages for the crop variety.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing crop_info and growth_stages
        """
        # Load prompt template from file
        prompt_content = load_prompt_template("stage2_growth_stages_research.md")
        query_template = extract_prompt_section(prompt_content, "プロンプトテンプレート")
        notes = extract_prompt_section(prompt_content, "注意事項")
        criteria = extract_prompt_section(prompt_content, "判定基準")
        
        # Combine instruction sections
        instruction = f"{notes}\n\n{criteria}"
        
        # Replace placeholders
        query = query_template.replace("{作物名}", crop_name).replace("{品種名}", variety)
        
        structure = {
            "crop_info": {
                "name": None,
                "variety": None
            },
            "growth_periods": [
                {
                    "period_name": None,
                    "order": None,
                    "period_description": None
                }
            ]
        }
        
        result = await self.llm_client.struct(query, structure, instruction)
        debug_print(f"Step 2 result: {result['data']}")
        return result.get("data", {})

    async def research_stage_requirements(self, crop_name: str, variety: str, 
                                         stage_name: str, stage_description: str) -> Dict[str, Any]:
        """Step 3: Research variety-specific requirements for a specific stage.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            stage_name: Name of the growth stage
            stage_description: Description of the growth stage
            
        Returns:
            Dict containing detailed requirements for the stage
        """
        # Load prompt template from file
        prompt_content = load_prompt_template("stage3_variety_specific_research.md")
        
        # Extract query template (from プロンプトテンプレート section)
        query_template = extract_prompt_section(prompt_content, "プロンプトテンプレート")
        
        # Replace placeholders
        query = query_template.replace("{作物名}", crop_name).replace("{品種名}", variety).replace("{期間名}", stage_name).replace("{具体的な特徴}", stage_description)
        
        # Extract instruction sections
        investigation_items = extract_prompt_section(prompt_content, "調査項目")
        sunshine_guide = extract_prompt_section(prompt_content, "日照時間設定の調査方針")
        notes = extract_prompt_section(prompt_content, "注意事項")
        
        # Combine instruction sections
        instruction = f"{investigation_items}\n\n{sunshine_guide}\n\n{notes}"
        
        structure = {
            "temperature": {
                "base_temperature": None,
                "optimal_min": None,
                "optimal_max": None,
                "low_stress_threshold": None,
                "high_stress_threshold": None,
                "frost_threshold": None,
                "sterility_risk_threshold": None
            },
            "sunshine": {
                "minimum_sunshine_hours": None,
                "target_sunshine_hours": None
            },
            "thermal": {
                "required_gdd": None
            }
        }
        
        result = await self.llm_client.struct(query, structure, instruction)
        debug_print(f"Step 3 result for {stage_name}: {result['data']}")
        return result.get("data", {})

    async def extract_crop_economics(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop economic information (area per unit and revenue per area).
        
        This is a separate LLM call independent from growth stage information.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing area_per_unit and revenue_per_area
        """
        query = f"""作物: {crop_name}
品種: {variety}

この作物・品種について、以下の経済情報を調査してください：
1. area_per_unit: 1単位あたりの栽培面積（㎡）
   - 例: トマトの場合、1株あたり何㎡必要か
   - 標準的な栽培密度から計算してください
2. revenue_per_area: 1㎡あたりの収益（円/㎡）
   - 例: 平均的な市場価格と収量から計算した㎡あたりの収益
   - 一般的な露地栽培または施設栽培での標準値を使用してください

数値のみを返してください（説明文は不要）。"""

        structure = {
            "area_per_unit": None,  # m² per unit
            "revenue_per_area": None  # yen per m²
        }
        
        instruction = """
        作物・品種の経済情報を調査し、JSON形式で返してください。
        - area_per_unit: 1単位（1株、1本など）あたりの栽培面積（㎡）
        - revenue_per_area: 1㎡あたりの収益（円/㎡）
        
        信頼できる農業資料や標準的な栽培データに基づいて数値を算出してください。
        数値は小数点以下も含めて正確に記載してください。
        """
        
        result = await self.llm_client.struct(query, structure, instruction)
        debug_print(f"Crop economics result: {result['data']}")
        return result.get("data", {})

    async def extract_crop_family(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop family (科) information.
        
        This is a separate LLM call to get the botanical family of the crop.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing family (科) information
        """
        query = f"""作物: {crop_name}
品種: {variety}

この作物の植物学的な科（family）を調査してください。
例:
- トマト → ナス科（Solanaceae）
- キュウリ → ウリ科（Cucurbitaceae）
- イネ → イネ科（Poaceae）

日本語の科名と学名の両方を返してください。"""

        structure = {
            "family_ja": None,  # Japanese family name (e.g., "ナス科")
            "family_scientific": None  # Scientific family name (e.g., "Solanaceae")
        }
        
        instruction = """
        作物の植物学的な科（family）を調査し、JSON形式で返してください。
        - family_ja: 日本語の科名（例: "ナス科"）
        - family_scientific: 学名（例: "Solanaceae"）
        
        正確な植物分類学に基づいて科名を返してください。
        """
        
        result = await self.llm_client.struct(query, structure, instruction)
        debug_print(f"Crop family result: {result['data']}")
        return result.get("data", {})

