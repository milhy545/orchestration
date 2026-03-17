"""Tests for Gemini provider token counting implementation."""

import unittest
from unittest.mock import Mock, patch
import sys

# Mock all dependencies BEFORE importing providers
sys.modules["google"] = Mock()
sys.modules["google.genai"] = Mock()
sys.modules["google.genai.types"] = Mock()
sys.modules["openai"] = Mock()
sys.modules["redis"] = Mock()
sys.modules["mcp"] = Mock()
sys.modules["mcp.server"] = Mock()
sys.modules["mcp.server.fastmcp"] = Mock()

from providers.gemini import GeminiModelProvider

class TestGeminiCountTokens(unittest.TestCase):
    """Test Gemini provider token counting."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = GeminiModelProvider("test-key")

    def test_count_tokens_success(self):
        """Test successful token counting using the SDK."""
        # Mock the client and its models.count_tokens method
        mock_client = Mock()
        mock_response = Mock()
        mock_response.total_tokens = 42
        mock_client.models.count_tokens.return_value = mock_response

        # Patch the client property
        with patch.object(GeminiModelProvider, 'client', mock_client):
            count = self.provider.count_tokens("Hello, world!", "gemini-2.5-flash")

            self.assertEqual(count, 42)
            mock_client.models.count_tokens.assert_called_once_with(
                model="gemini-2.5-flash",
                contents="Hello, world!"
            )

    def test_count_tokens_fallback(self):
        """Test fallback to estimation when the SDK call fails."""
        mock_client = Mock()
        mock_client.models.count_tokens.side_effect = Exception("API Error")

        with patch.object(GeminiModelProvider, 'client', mock_client):
            # Test text with 20 characters should result in 20 // 4 = 5 tokens
            text = "12345678901234567890"
            count = self.provider.count_tokens(text, "gemini-2.5-flash")

            self.assertEqual(count, 5)

    def test_count_tokens_caching(self):
        """Test that token counts are cached."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.total_tokens = 10
        mock_client.models.count_tokens.return_value = mock_response

        with patch.object(GeminiModelProvider, 'client', mock_client):
            text = "Cache me"
            # First call
            count1 = self.provider.count_tokens(text, "gemini-2.5-flash")
            # Second call
            count2 = self.provider.count_tokens(text, "gemini-2.5-flash")

            self.assertEqual(count1, 10)
            self.assertEqual(count2, 10)
            # Should only be called once due to caching
            self.assertEqual(mock_client.models.count_tokens.call_count, 1)

if __name__ == "__main__":
    unittest.main()
