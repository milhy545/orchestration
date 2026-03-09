import importlib.util
from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
spec = importlib.util.spec_from_file_location("vault_ui_app", APP_PATH)
vault_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vault_app)  # type: ignore[call-arg]


def test_common_mcp_includes_notion_key():
    common = vault_app.SERVICE_CONFIGS.get("common-mcp", {})
    assert "runtime_keys" in common
    assert "NOTION_API_KEY" in common["runtime_keys"]
    assert common["vault_path"] == "orchestration/common-mcp"


def test_render_ui_includes_cockpit_title():
    html = vault_app._render_ui_html()
    assert "<title>Server Cockpit</title>" in html
    assert "data-i18n-key=\"dashboardEyebrow\"" in html
