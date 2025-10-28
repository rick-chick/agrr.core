"""Framework LLM client implementation.

Implements the `LLMClient` contract using OpenAI API with proper environment variable management.
Provides generic struct() method for structured data extraction from LLM.
"""

import os
import json
from typing import Dict, Any, Optional

from agrr_core.adapter.interfaces.clients.llm_client_interface import LLMClientInterface

# Conditional imports
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Load environment variables from .env file if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use environment variables directly
    pass


class LLMClient(LLMClientInterface):
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

            # Check if websearch is enabled
            websearch_enabled = os.getenv("OPENAI_WEBSEARCH_ENABLED", "false").lower() == "true"
            
            # Use Responses API if websearch is enabled, otherwise use chat.completions
            if websearch_enabled:
                # Use Responses API with web_search_preview tool
                response = await client.responses.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                    tools=[{"type": "web_search_preview"}],
                    input=f"{system_prompt}\n\n{query}\n\nPlease respond in JSON format."
                )
                
                # Extract content from responses API
                content = response.output_text if hasattr(response, 'output_text') else str(response)
                
                # Extract JSON from markdown code block if present
                if content.startswith('```json'):
                    # Remove markdown code block markers
                    lines = content.split('\n')
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.strip() == '```json':
                            in_json = True
                            continue
                        elif line.strip() == '```':
                            break
                        elif in_json:
                            json_lines.append(line)
                    content = '\n'.join(json_lines)
                
                # Parse as JSON
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSON parse error: {e}")
                    print(f"[DEBUG] Content: {content}")
                    raise RuntimeError(f"Failed to parse JSON response from OpenAI Responses API: {str(e)}")
                
                return {"provider": "openai_responses", "data": data, "schema": schema}
            else:
                # Use chat.completions API with JSON response format
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
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

