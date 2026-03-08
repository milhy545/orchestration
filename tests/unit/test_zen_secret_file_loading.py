from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path("/home/orchestration")


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
        "provider_registry": PROJECT_ROOT / "mcp-servers" / "zen-mcp" / "providers" / "registry.py",
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

    assert 'from utils.secrets import load_env' in sources["provider_registry"]
    assert 'return load_env(env_var)' in sources["provider_registry"]
    assert 'load_env("CUSTOM_API_URL", "")' in sources["provider_registry"]

    assert 'from utils.secrets import load_env' in sources["custom_provider"]
    assert 'load_env("CUSTOM_API_URL", "")' in sources["custom_provider"]
    assert 'load_env("CUSTOM_API_KEY", "")' in sources["custom_provider"]

    assert 'from utils.secrets import load_env' in sources["listmodels"]
    assert 'load_env("OPENROUTER_API_KEY")' in sources["listmodels"]

    assert 'from utils.secrets import load_env' in sources["shared_base_tool"]
    assert 'load_env("OPENROUTER_API_KEY")' in sources["shared_base_tool"]

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
