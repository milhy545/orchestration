from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _import_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_zen_secret_helper_prefers_file(tmp_path, monkeypatch) -> None:
    module = _import_module(
        "zen_mcp_utils_secrets_test",
        PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "utils" / "secrets.py",
    )
    secret_file = tmp_path / "openrouter.key"
    secret_file.write_text("from-file\n", encoding="utf-8")
    monkeypatch.setenv("OPENROUTER_API_KEY", "from-env")
    monkeypatch.setenv("OPENROUTER_API_KEY_FILE", str(secret_file))

    assert module.load_env("OPENROUTER_API_KEY") == "from-file"


def test_zen_runtime_sources_use_file_aware_loader() -> None:
    files = {
        "server": PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "server.py",
        "config": PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "config.py",
        "provider_registry": PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "providers" / "registry.py",
        "dial_provider": PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "providers" / "dial.py",
        "custom_provider": PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "providers" / "custom.py",
        "listmodels": PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "tools" / "listmodels.py",
        "shared_base_tool": PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "tools" / "shared" / "base_tool.py",
        "base_tool": PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "tools" / "base.py",
    }
    sources = {name: path.read_text(encoding="utf-8") for name, path in files.items()}

    assert 'from utils.secrets import load_env' in sources["server"]
    assert 'load_env("GEMINI_API_KEY")' in sources["server"]
    assert 'load_env("OPENAI_API_KEY")' in sources["server"]
    assert 'load_env("XAI_API_KEY")' in sources["server"]
    assert 'load_env("OPENROUTER_API_KEY")' in sources["server"]
    assert 'load_env("CUSTOM_API_KEY", "")' in sources["server"]
    assert 'load_env("DEFAULT_MODEL", "auto")' in sources["config"]
    assert 'load_env("MAX_MCP_OUTPUT_TOKENS")' in sources["config"]

    assert 'from utils.secrets import load_env' in sources["provider_registry"]
    assert 'return load_env(env_var)' in sources["provider_registry"]
    assert 'load_env("CUSTOM_API_URL", "")' in sources["provider_registry"]
    assert 'load_env("DIAL_API_HOST")' in sources["dial_provider"]
    assert (
        'load_env("DIAL_API_VERSION", "2024-12-01-preview")'
        in sources["dial_provider"]
    )

    assert 'from utils.secrets import load_env' in sources["custom_provider"]
    assert 'load_env("CUSTOM_API_URL", "")' in sources["custom_provider"]
    assert 'load_env("CUSTOM_API_KEY", "")' in sources["custom_provider"]

    assert 'from utils.secrets import load_env' in sources["listmodels"]
    assert 'load_env("OPENROUTER_API_KEY")' in sources["listmodels"]
    assert 'load_env("CUSTOM_API_URL")' in sources["listmodels"]

    assert 'from utils.secrets import load_env' in sources["shared_base_tool"]
    assert 'load_env("OPENROUTER_API_KEY")' in sources["shared_base_tool"]
    assert sources["shared_base_tool"].count('load_env("CUSTOM_API_URL")') == 2

    assert 'from utils.secrets import load_env' in sources["base_tool"]
    assert 'load_env("OPENROUTER_API_KEY")' in sources["base_tool"]


def test_zen_vault_delivery_mode_is_file_based() -> None:
    payload = json.loads(
        (PROJECT_ROOT / "services" / "vault-secrets-ui" / "services.json").read_text(
            encoding="utf-8"
        )
    )
    services = {service["id"]: service for service in payload["services"]}
    assert services["zen-mcp-server"]["delivery_mode"] == "file"

    renderer = (PROJECT_ROOT / "infra" / "vault" / "render-envs.sh").read_text(encoding="utf-8")
    assert '"zen-mcp-server"' in renderer
    assert '"file"' in renderer


def test_zen_healthcheck_accepts_file_delivered_api_key(tmp_path, monkeypatch) -> None:
    module = _import_module(
        "zen_mcp_healthcheck_test",
        PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "docker" / "scripts" / "healthcheck.py",
    )
    api_keys = [
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "XAI_API_KEY",
        "DIAL_API_KEY",
        "OPENROUTER_API_KEY",
    ]
    for key in api_keys:
        monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv(f"{key}_FILE", raising=False)

    api_key_file = tmp_path / "gemini.key"
    api_key_file.write_text("long-enough-test-key\n", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY_FILE", str(api_key_file))

    assert module.check_environment()


def test_zen_healthcheck_rejects_missing_secret_file(tmp_path, monkeypatch) -> None:
    module = _import_module(
        "zen_mcp_healthcheck_missing_file_test",
        PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "docker" / "scripts" / "healthcheck.py",
    )
    api_keys = [
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "XAI_API_KEY",
        "DIAL_API_KEY",
        "OPENROUTER_API_KEY",
    ]
    for key in api_keys:
        monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv(f"{key}_FILE", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY_FILE", str(tmp_path / "missing.key"))

    assert not module.check_environment()


def test_zen_config_loads_model_and_token_limit_from_files(tmp_path) -> None:
    zen_root = PROJECT_ROOT / "mcp-servers" / "zen-mcp"
    model_file = tmp_path / "default-model"
    token_limit_file = tmp_path / "max-output-tokens"
    model_file.write_text("gemini-2.5-pro\n", encoding="utf-8")
    token_limit_file.write_text("1000\n", encoding="utf-8")

    env = os.environ.copy()
    env.pop("DEFAULT_MODEL", None)
    env.pop("MAX_MCP_OUTPUT_TOKENS", None)
    env["DEFAULT_MODEL_FILE"] = str(model_file)
    env["MAX_MCP_OUTPUT_TOKENS_FILE"] = str(token_limit_file)
    env["PYTHONPATH"] = str(zen_root)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import config; assert config.DEFAULT_MODEL == 'gemini-2.5-pro'; "
            "assert config.MCP_PROMPT_SIZE_LIMIT == 2400",
        ],
        cwd=zen_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
