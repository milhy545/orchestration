import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Mock modules before importing MegaOrchestrator
mock_aiohttp = MagicMock()
mock_asyncpg = MagicMock()
mock_aioredis = MagicMock()
sys.modules["aiohttp"] = mock_aiohttp
sys.modules["aiohttp.web"] = MagicMock()
sys.modules["asyncpg"] = mock_asyncpg
sys.modules["redis"] = MagicMock()
sys.modules["redis.asyncio"] = mock_aioredis
sys.modules["aiofiles"] = MagicMock()

from mega_orchestrator.mega_orchestrator_complete import MegaOrchestrator

class TestSecurityJWT(unittest.TestCase):
    def setUp(self):
        # We need to mock components that are initialized in __init__
        with patch('mega_orchestrator.mega_orchestrator_complete.ConversationMemory'), \
             patch('mega_orchestrator.mega_orchestrator_complete.FileStorage'), \
             patch('mega_orchestrator.mega_orchestrator_complete.ChatRecall'), \
             patch('mega_orchestrator.mega_orchestrator_complete.WelcomeService'), \
             patch('mega_orchestrator.mega_orchestrator_complete.SAGEModeRouter'):
            self.orchestrator = MegaOrchestrator()

    def test_get_marketplace_token_no_fallback(self):
        """Test that the orchestrator no longer falls back to a hardcoded secret and raises RuntimeError."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure MARKETPLACE_JWT_TOKEN is not in env
            self.assertNotIn("MARKETPLACE_JWT_TOKEN", os.environ)

            with self.assertRaises(RuntimeError) as cm:
                self.orchestrator._get_marketplace_token()

            self.assertIn("MARKETPLACE_JWT_TOKEN is not configured", str(cm.exception))

    def test_get_marketplace_token_from_env(self):
        """Test that the orchestrator uses the token from the environment variable if present."""
        test_token = "env_provided_token"
        with patch.dict(os.environ, {"MARKETPLACE_JWT_TOKEN": test_token}):
            token = self.orchestrator._get_marketplace_token()
            self.assertEqual(token, test_token)

if __name__ == "__main__":
    unittest.main()
