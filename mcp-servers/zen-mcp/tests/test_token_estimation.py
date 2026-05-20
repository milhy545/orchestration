import unittest
from unittest.mock import Mock, patch
import sys
import os

# Mock problematic modules before imports
sys.modules["google"] = Mock()
sys.modules["google.genai"] = Mock()
sys.modules["openai"] = Mock()

# Add the zen-mcp directory to sys.path to allow imports
zen_mcp_path = os.path.join(os.getcwd(), "mcp-servers", "zen-mcp")
if zen_mcp_path not in sys.path:
    sys.path.append(zen_mcp_path)

from utils.model_context import ModelContext

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

        # When provider is accessed in estimate_tokens via self.provider property,
        # it should raise a ValueError if no provider found.
        # Let's check how self.provider is implemented.

        text = "Hello world"

        # In current implementation of ModelContext.provider:
        # if not self._provider:
        #     self._provider = ModelProviderRegistry.get_provider_for_model(self.model_name)
        #     if not self._provider:
        #         raise ValueError(...)

        # So estimate_tokens should catch this ValueError and fallback.
        tokens = self.ctx.estimate_tokens(text)
        self.assertEqual(tokens, 3)

if __name__ == "__main__":
    unittest.main()
