import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "marketplace" / "speak_via_elevenlabs_mcp.py"
SPEC = importlib.util.spec_from_file_location("speak_via_elevenlabs_mcp", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
load_env_file = MODULE.load_env_file


def test_load_env_file_strips_single_quotes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    env_file = tmp_path / "elevenlabs.env"
    env_file.write_text("ELEVENLABS_API_KEY='sk_test_123'\n", encoding="utf-8")

    load_env_file(env_file)

    assert __import__("os").environ["ELEVENLABS_API_KEY"] == "sk_test_123"


def test_load_env_file_strips_double_quotes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    env_file = tmp_path / "elevenlabs.env"
    env_file.write_text('ELEVENLABS_API_KEY="sk_test_456"\n', encoding="utf-8")

    load_env_file(env_file)

    assert __import__("os").environ["ELEVENLABS_API_KEY"] == "sk_test_456"
