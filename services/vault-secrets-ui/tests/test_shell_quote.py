import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock dependencies that are not available in the test environment or cause issues on import
sys.modules["httpx"] = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.responses"] = MagicMock()
sys.modules["pydantic"] = MagicMock()

# Import app.py by file path because vault-secrets-ui is not an importable
# package name when tests are run from the repository root.
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
spec = importlib.util.spec_from_file_location("vault_secrets_ui_app", APP_PATH)
app_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app_module
assert spec.loader is not None
spec.loader.exec_module(app_module)
_shell_quote = app_module._shell_quote


def test_shell_quote_simple():
    assert _shell_quote("hello") == "'hello'"


def test_shell_quote_with_spaces():
    assert _shell_quote("hello world") == "'hello world'"


def test_shell_quote_with_single_quotes():
    # In POSIX shell, to include a single quote ' inside a single-quoted string,
    # you have to end the current single-quoted string, add a quoted single quote,
    # and then start a new single-quoted string.
    # ' -> '"'"'
    # "it's" -> "'it'\"'\"'s'"
    assert _shell_quote("it's") == "'it'\"'\"'s'"


def test_shell_quote_empty():
    assert _shell_quote("") == "''"


def test_shell_quote_multiple_quotes():
    # "a'b'c" -> "'a'\"'\"'b'\"'\"'c'"
    assert _shell_quote("a'b'c") == "'a'\"'\"'b'\"'\"'c'"


def test_shell_quote_with_double_quotes():
    assert _shell_quote('hello "world"') == "'hello \"world\"'"
