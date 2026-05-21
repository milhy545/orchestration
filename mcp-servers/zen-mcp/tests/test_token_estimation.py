import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock problematic modules before imports
sys.modules["google"] = Mock()
sys.modules["google.genai"] = Mock()
sys.modules["openai"] = Mock()
sys.modules["httpx"] = Mock()

# Add the zen-mcp directory to sys.path to allow imports
zen_mcp_path = os.path.join(os.getcwd(), "mcp-servers", "zen-mcp")
if zen_mcp_path not in sys.path:
    sys.path.append(zen_mcp_path)

from utils.model_context import ModelContext
from providers.openai_compatible import OpenAICompatibleProvider

class TestTokenEstimation(unittest.TestCase):
    def setUp(self):
        self.model_name = "test-model"
        self.ctx = ModelContext(self.model_name)

    @patch("providers.registry.ModelProviderRegistry.get_provider_for_model")
    def test_estimate_tokens_delegation(self, mock_get_provider):
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.count_tokens.return_value = 42
        mock_get_provider.return_value = mock_provider

        text = "Hello world"
        tokens = self.ctx.estimate_tokens(text)

        # Verify delegation
        mock_provider.count_tokens.assert_called_once_with(text, self.model_name)
        self.assertEqual(tokens, 42)

    @patch("providers.registry.ModelProviderRegistry.get_provider_for_model")
    def test_estimate_tokens_fallback_on_exception(self, mock_get_provider):
        # Setup mock provider that raises an exception
        mock_provider = Mock()
        mock_provider.count_tokens.side_effect = Exception("Counting failed")
        mock_get_provider.return_value = mock_provider

        text = "Hello world" # 11 chars
        tokens = self.ctx.estimate_tokens(text)

        # Verify fallback (11 // 3 = 3)
        self.assertEqual(tokens, 3)

    @patch("providers.registry.ModelProviderRegistry.get_provider_for_model")
    def test_estimate_tokens_fallback_no_provider(self, mock_get_provider):
        # Setup registry to return no provider
        mock_get_provider.return_value = None

        text = "Hello world"
        tokens = self.ctx.estimate_tokens(text)
        self.assertEqual(tokens, 3)

    def test_openai_compatible_provider_count_tokens_with_tiktoken(self):
        """Test that OpenAICompatibleProvider correctly uses tiktoken and caches results."""
        # We must set up tiktoken BEFORE creating the provider if it uses it in __init__
        # but it doesn't. However, it's safer.
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2, 3] # 3 tokens

        mock_tiktoken = Mock()
        mock_tiktoken.get_encoding.return_value = mock_encoding
        mock_tiktoken.encoding_for_model.return_value = mock_encoding
        sys.modules["tiktoken"] = mock_tiktoken

        class ConcreteProvider(OpenAICompatibleProvider):
            def get_capabilities(self, model_name): return Mock()
            def get_provider_type(self): return Mock()
            def validate_model_name(self, model_name): return True

        provider = ConcreteProvider(api_key="test")

        text = "test text"

        # First call - should call tiktoken
        count1 = provider.count_tokens(text, "gpt-4")
        self.assertEqual(count1, 3)
        # It might call encoding_for_model OR get_encoding
        self.assertTrue(mock_tiktoken.encoding_for_model.called or mock_tiktoken.get_encoding.called)

        # Second call - should use cache
        mock_tiktoken.get_encoding.reset_mock()
        mock_tiktoken.encoding_for_model.reset_mock()
        count2 = provider.count_tokens(text, "gpt-4")
        self.assertEqual(count2, 3)
        mock_tiktoken.get_encoding.assert_not_called()
        mock_tiktoken.encoding_for_model.assert_not_called()

if __name__ == "__main__":
    unittest.main()
