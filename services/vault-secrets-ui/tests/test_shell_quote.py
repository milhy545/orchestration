import sys
from unittest.mock import MagicMock

# Mock dependencies that are not available in the test environment or cause issues on import
sys.modules["httpx"] = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.responses"] = MagicMock()
sys.modules["pydantic"] = MagicMock()

# Now we can import the function to test
from app import _shell_quote

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
