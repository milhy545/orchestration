"""
Tests for the debug tool using new architecture.
"""

import pytest
from tools.debug import DebugIssueRequest, DebugIssueTool
from tools.models import ToolModelCategory


class TestDebugTool:
    """Test suite for DebugIssueTool using new architecture."""

    def setup_method(self):
        """Set up test fixtures"""
        self.tool = DebugIssueTool()

    def test_tool_metadata(self):
        """Test basic tool metadata and configuration."""
        assert self.tool.get_name() == "debug"
        assert "DEBUG - Root cause analysis" in self.tool.get_description()
        assert self.tool.get_default_temperature() == 0.2  # TEMPERATURE_ANALYTICAL
        assert self.tool.get_model_category() == ToolModelCategory.EXTENDED_REASONING
        assert self.tool.requires_model() is True

    def test_request_validation(self):
        """Test Pydantic request model validation."""
        # Valid debug request
        request = DebugIssueRequest(
            prompt="Null pointer exception in UserService",
            error_context="java.lang.NullPointerException at UserService.java:45",
            files=["/src/UserService.java"],
            runtime_info="Java 17, Spring Boot 3.0",
            previous_attempts="Tried restarting the service",
        )

        assert request.prompt == "Null pointer exception in UserService"
        assert request.error_context == "java.lang.NullPointerException at UserService.java:45"
        assert request.files == ["/src/UserService.java"]

    def test_required_fields(self):
        """Test that required fields are enforced."""
        from pydantic import ValidationError
        
        # Missing prompt should raise validation error
        with pytest.raises(ValidationError):
            DebugIssueRequest(error_context="some error")

    def test_input_schema_generation(self):
        """Test that input schema is generated correctly."""
        schema = self.tool.get_input_schema()

        # Verify required fields are present
        assert "prompt" in schema["properties"]
        assert "error_context" in schema["properties"]
        assert "files" in schema["properties"]
        assert "runtime_info" in schema["properties"]
        assert "previous_attempts" in schema["properties"]

        # Verify field types
        assert schema["properties"]["prompt"]["type"] == "string"
        assert schema["properties"]["files"]["type"] == "array"

    def test_model_category_for_debugging(self):
        """Test that debug tool correctly identifies as extended reasoning category."""
        assert self.tool.get_model_category() == ToolModelCategory.EXTENDED_REASONING

    @pytest.mark.asyncio
    async def test_prompt_preparation(self):
        """Test that prompt preparation works correctly."""
        request = DebugIssueRequest(
            prompt="Test issue",
            error_context="Test context",
            files=["/abs/path/file.py"]
        )
        
        # Mock necessary methods to avoid actual file system/token checks
        from unittest.mock import patch
        with patch.object(self.tool, "get_system_prompt", return_value="System prompt"):
            with patch.object(self.tool, "handle_prompt_file", return_value=(None, None)):
                with patch.object(self.tool, "_prepare_file_content_for_prompt", return_value=("File content", ["/abs/path/file.py"], None)):
                    with patch.object(self.tool, "_validate_token_limit"):
                        with patch.object(self.tool, "get_websearch_instruction", return_value=""):
                            prompt = await self.tool.prepare_prompt(request)
                            
                            assert "Test issue" in prompt
                            assert "Test context" in prompt
                            assert "File content" in prompt
                            assert "System prompt" in prompt
