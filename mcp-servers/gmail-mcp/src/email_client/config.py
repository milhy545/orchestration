import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging (optional here, but good practice if config needs logging)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the directory where this config file is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Load environment variables from .env file in the same directory
dotenv_path = os.path.join(script_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    # Attempt to load from parent directory if .env is in the project root
    parent_dotenv_path = os.path.join(os.path.dirname(script_dir), '.env')
    if os.path.exists(parent_dotenv_path):
        load_dotenv(parent_dotenv_path)
    # else:
        # logging.warning(".env file not found in standard locations.") # Optional warning

# Email configuration
def _load_setting(name: str, default: str) -> str:
    file_path = os.getenv(f"{name}_FILE", "").strip()
    if file_path:
        value = Path(file_path).read_text(encoding="utf-8").strip()
        return value or default
    return os.getenv(name, default)


EMAIL_CONFIG = {
    "email": _load_setting("EMAIL_ADDRESS", "your.email@gmail.com"),
    "password": _load_setting("EMAIL_PASSWORD", "your-app-specific-password"),
    "imap_server": _load_setting("IMAP_SERVER", "imap.gmail.com"),
    "smtp_server": _load_setting("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(_load_setting("SMTP_PORT", "587"))
}

# Constants
SEARCH_TIMEOUT = 120  # seconds
DEFAULT_MAX_EMAILS = 20  # Default limit for email search results

# Basic validation (optional)
# if not EMAIL_CONFIG["email"] or not EMAIL_CONFIG["password"]:
#     logging.warning("Email address or password not configured in environment variables.")
