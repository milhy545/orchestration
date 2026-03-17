import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib

# Mock psycopg2 before importing the scripts
sys.modules['psycopg2'] = MagicMock()

def load_config_from_file(filepath):
    import importlib.util
    module_name = "test_module_" + os.path.basename(filepath).replace('-', '_').replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.POSTGRES_CONFIG

class TestMigrationConfig(unittest.TestCase):
    def test_config_loading(self):
        # Mock environment variables
        env_vars = {
            "POSTGRES_HOST": "test-host",
            "POSTGRES_PORT": "5433",
            "POSTGRES_DB": "test-db",
            "POSTGRES_USER": "test-user",
            "POSTGRES_PASSWORD": "test-password"
        }

        with patch.dict(os.environ, env_vars):
            config1 = load_config_from_file("scripts/migrate-to-postgresql.py")
            self.assertEqual(config1["host"], "test-host")
            self.assertEqual(config1["port"], 5433)
            self.assertEqual(config1["database"], "test-db")
            self.assertEqual(config1["user"], "test-user")
            self.assertEqual(config1["password"], "test-password")

            config2 = load_config_from_file("scripts/migrate_sqlite_to_postgres.py")
            self.assertEqual(config2["host"], "test-host")
            self.assertEqual(config2["port"], 5433)
            self.assertEqual(config2["database"], "test-db")
            self.assertEqual(config2["user"], "test-user")
            self.assertEqual(config2["password"], "test-password")

    def test_config_defaults(self):
        # Ensure it doesn't crash if env vars are missing
        with patch.dict(os.environ, {}, clear=True):
            config1 = load_config_from_file("scripts/migrate-to-postgresql.py")
            self.assertEqual(config1["host"], "localhost")
            self.assertIsNone(config1["password"])

if __name__ == "__main__":
    unittest.main()
