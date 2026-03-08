from pathlib import Path

from vault_secrets_ui.app_factory import create_app

BASE_DIR = Path(__file__).resolve().parent

app = create_app(
    config_path=BASE_DIR / "services.json",
    template_path=BASE_DIR / "src" / "vault_secrets_ui" / "templates" / "vault_webui.html",
)
