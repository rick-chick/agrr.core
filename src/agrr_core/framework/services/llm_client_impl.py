"""Framework LLM client implementation.

Implements the `LLMClient` contract. If OpenAI SDK and API key are available,
uses the async client with JSON schema response (and enables search tool-call
when supported). Falls back to a structured stub otherwise.
"""

import os
from typing import Dict, Any, Optional

from agrr_core.adapter.interfaces.llm_client import LLMClient


class FrameworkLLMClient(LLMClient):
    """LLM client that prefers OpenAI JSON schema, else returns a stub."""

    async def struct(self, query: str, structure: Dict[str, Any], instruction: Optional[str] = None) -> Dict[str, Any]:
        # Try OpenAI first
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is not None:
            try:
                # Import lazily to avoid hard dependency if unused
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=api_key)

                # Convert provider-agnostic structure to JSON Schema (shallow conversion)
                def to_json_schema(node: Any) -> Dict[str, Any]:  # type: ignore[name-defined]
                    import collections.abc as _abc

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

                # Some SDKs support response_format with json_schema, newer clients may differ.
                # Use the Responses API if available; otherwise, fall back to chat.completions with json response.
                try:
                    # Prefer Responses API with JSON schema and web search tool when supported.
                    # Note: This block may vary depending on installed openai SDK version.
                    resp = await client.responses.create(
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        input=query,
                        system=system_prompt,
                        response_format={"type": "json_schema", "json_schema": wrapped_schema},
                        tools=[{"type": "web_search"}],
                        tool_choice={"type": "auto"},
                    )
                    # Extract JSON content
                    data = None
                    if resp and getattr(resp, "output", None):
                        # Newer SDK shape
                        for item in resp.output:
                            if getattr(item, "type", None) == "output_text":
                                # Some models might return text; ignore here
                                continue
                            if getattr(item, "type", None) == "output_json":
                                data = item.output
                                break
                    if data is None and getattr(resp, "output_text", None):
                        # As a fallback, try to parse text as JSON if possible
                        try:
                            import json as _json

                            data = _json.loads(resp.output_text)
                        except Exception:
                            data = None
                    if data is not None:
                        return {"provider": "openai", "data": data, "schema": schema}
                except Exception:
                    # Fall back to chat.completions if responses API is not available
                    pass

                # Fallback to a minimal JSON response using chat.completions
                try:
                    from openai import AsyncOpenAI as _AsyncOpenAI

                    chat = _AsyncOpenAI(api_key=api_key)
                    import json as _json

                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": _json.dumps({"query": query, "structure": structure})})
                    cmpl = await chat.chat.completions.create(
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        messages=messages,
                        temperature=0,
                    )
                    content = cmpl.choices[0].message.content if cmpl.choices else None
                    data = None
                    if content:
                        try:
                            data = _json.loads(content)
                        except Exception:
                            data = None
                    if data is not None:
                        return {"provider": "openai", "data": data, "schema": schema}
                except Exception:
                    # If OpenAI call fails, fall through to stub
                    pass
            except Exception:
                # OpenAI not usable; fall through to stub
                pass

        # Stub: echo schema with placeholders
        # Stub: fill from structure keys if present
        result: Dict[str, Any] = {}
        try:
            for key in structure.keys():
                result[key] = None
        except Exception:
            pass
        result["_query"] = query
        if instruction:
            result["_instruction"] = instruction
        return {"provider": "stub", "data": result, "structure": structure}


