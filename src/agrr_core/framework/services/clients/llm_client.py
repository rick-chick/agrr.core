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
    # Use synchronous client to avoid async httpx close issues
    from openai import OpenAI
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

    def struct(self, query: str, structure: Dict[str, Any], instruction: Optional[str] = None) -> Dict[str, Any]:
        # Check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file or environment.")
        
        # Use OpenAI API
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI library is not installed. Please install it with: pip install openai")
        
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

        system_prompt = instruction or ""
        websearch_enabled = os.getenv("OPENAI_WEBSEARCH_ENABLED", "false").lower() == "true"

        client = OpenAI(api_key=api_key)
        if websearch_enabled:
            resp = client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                tools=[{"type": "web_search_preview"}],
                input=f"{system_prompt}\n\n{query}\n\nPlease respond in JSON format."
            )
            text = getattr(resp, 'output_text', None)
            content = text if isinstance(text, str) else str(resp)
            provider = "openai_responses"
        else:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            user_message = f"{query}\n\nPlease respond in JSON format."
            messages.append({"role": "user", "content": user_message})
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content if resp.choices else None
            provider = "openai"

        if not content:
            raise RuntimeError("No response content from OpenAI API")

        # Extract JSON from markdown code block if present
        if isinstance(content, str) and content.startswith('```json'):
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

        try:
            data = json.loads(content)  # type: ignore[arg-type]
            return {"provider": provider, "data": data, "schema": schema}
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON response from OpenAI: {str(e)}")

