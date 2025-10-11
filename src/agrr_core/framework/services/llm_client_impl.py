"""Framework LLM client implementation.

Implements the `LLMClient` contract using OpenAI API with proper environment variable management.

Provides the 3-step crop requirement research methods:
1. Step 1: Crop variety selection
2. Step 2: Growth stage definition
3. Step 3: Variety-specific requirement research and structuring

Note: The orchestration of these steps is handled by the UseCase layer (Interactor),
not by this Framework layer component.
"""

import os
import json
import collections.abc
from pathlib import Path
from typing import Dict, Any, Optional, List

from agrr_core.adapter.interfaces.llm_client import LLMClient

# Conditional imports
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

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
    # Get the project root (assuming this file is in src/agrr_core/framework/services/)
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

# Load environment variables from .env file if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use environment variables directly
    pass


class FrameworkLLMClient(LLMClient):
    """LLM client using OpenAI API with proper environment variable management."""

    async def struct(self, query: str, structure: Dict[str, Any], instruction: Optional[str] = None) -> Dict[str, Any]:
        # Check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file or environment.")
        
        # Use OpenAI API
        try:
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI library is not installed. Please install it with: pip install openai")
            
            client = AsyncOpenAI(api_key=api_key)

            # Convert provider-agnostic structure to JSON Schema (shallow conversion)
            def to_json_schema(node: Any) -> Dict[str, Any]:  # type: ignore[name-defined]
                if isinstance(node, dict):
                    props = {k: to_json_schema(v) for k, v in node.items()}
                    return {"type": "object", "properties": props, "additionalProperties": False}
                if isinstance(node, list):
                    item = node[0] if node else {}
                    return {"type": "array", "items": to_json_schema(item)}
                # Scalars or None → allow number/string/null
                return {"type": ["number", "string", "null"]}

            schema = to_json_schema(structure)

            # Wrap for Responses API
            wrapped_schema = {
                "name": os.getenv("OPENAI_JSON_SCHEMA_NAME", "structured_output"),
                "schema": schema,
                "strict": True,
            }

            system_prompt = instruction or ""

            # Use chat.completions API with JSON response format
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            # Add JSON requirement for response_format
            user_message = f"{query}\n\nPlease respond in JSON format."
            messages.append({"role": "user", "content": user_message})
            
            response = await client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content if response.choices else None
            if not content:
                raise RuntimeError("No response content from OpenAI API")
            
            try:
                data = json.loads(content)
                return {"provider": "openai", "data": data, "schema": schema}
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Failed to parse JSON response from OpenAI: {str(e)}")
        except Exception as e:
            # If OpenAI setup fails, raise the error
            raise RuntimeError(f"Failed to initialize OpenAI client: {str(e)}")

    async def step1_crop_variety_selection(self, crop_query: str) -> Dict[str, Any]:
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
        
        result = await self.struct(crop_query, structure, instruction)
        debug_print(f"Step 1 result: {result['data']}")
        return result

    async def step2_growth_stage_definition(self, crop_name: str, variety: str) -> Dict[str, Any]:
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
        
        result = await self.struct(query, structure, instruction)
        debug_print(f"Step 2 result: {result['data']}")
        return result

    async def step3_variety_specific_research(self, crop_name: str, variety: str, 
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
        
        result = await self.struct(query, structure, instruction)
        debug_print(f"Step 3 result for {stage_name}: {result['data']}")
        return result

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
        
        result = await self.struct(query, structure, instruction)
        debug_print(f"Crop economics result: {result['data']}")
        return result