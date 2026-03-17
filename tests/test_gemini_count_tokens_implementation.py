import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add zen-mcp to path
sys.path.append(str(Path(__file__).parent.parent / 'mcp-servers' / 'zen-mcp'))

from providers.gemini import GeminiModelProvider

@pytest.fixture
def gemini_provider():
    return GeminiModelProvider(api_key="test-key")

@pytest.mark.asyncio
async def test_count_tokens_uses_sdk_and_caches(gemini_provider):
    """Test that count_tokens uses the Gemini SDK and caches results."""
    # Mock the Gemini client and its count_tokens method
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.total_tokens = 42
    mock_client.models.count_tokens.return_value = mock_response
    
    with patch.object(GeminiModelProvider, 'client', mock_client):
        # First call should use the SDK
        count1 = gemini_provider.count_tokens("Hello world", "gemini-2.0-flash")
        assert count1 == 42
        assert mock_client.models.count_tokens.call_count == 1
        
        # Second call with same text should use cache
        count2 = gemini_provider.count_tokens("Hello world", "gemini-2.0-flash")
        assert count2 == 42
        assert mock_client.models.count_tokens.call_count == 1  # Still 1

@pytest.mark.asyncio
async def test_count_tokens_fallback_on_error(gemini_provider):
    """Test that count_tokens falls back to estimation if SDK fails."""
    mock_client = MagicMock()
    mock_client.models.count_tokens.side_effect = Exception("API Error")
    
    test_text = "This is a test sentence with about 10 words."
    expected_fallback = len(test_text) // 4
    
    with patch.object(GeminiModelProvider, 'client', mock_client):
        count = gemini_provider.count_tokens(test_text, "gemini-2.0-flash")
        assert count == expected_fallback
        assert mock_client.models.count_tokens.call_count == 1

@pytest.mark.asyncio
async def test_count_tokens_empty_text(gemini_provider):
    """Test that count_tokens returns 0 for empty text."""
    assert gemini_provider.count_tokens("", "gemini-2.0-flash") == 0
    assert gemini_provider.count_tokens(None, "gemini-2.0-flash") == 0
