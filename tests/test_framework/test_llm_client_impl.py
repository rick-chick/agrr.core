"""Tests for FrameworkLLMClient."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from agrr_core.framework.services.clients.llm_client import LLMClient as FrameworkLLMClient


class TestFrameworkLLMClient:
    """Test cases for FrameworkLLMClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = FrameworkLLMClient()
    
    def test_init(self):
        """Test client initialization."""
        assert isinstance(self.client, FrameworkLLMClient)
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_struct_with_openai(self):
        """Test struct method with OpenAI API (requires OPENAI_API_KEY)."""
        structure = {"name": None, "value": None}
        query = "test query"
        instruction = "test instruction"
        
        result = await self.client.struct(query, structure, instruction)
        
        # Should return openai provider (since API key is configured)
        assert result["provider"] == "openai"
        assert "data" in result
        assert "schema" in result
    