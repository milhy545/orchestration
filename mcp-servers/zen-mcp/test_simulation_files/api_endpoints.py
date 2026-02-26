#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request
from markupsafe import escape
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["DEBUG"] = False
app.config["SECRET_KEY"] = "test-simulation-secret-key"

UPLOAD_ROOT = Path("/tmp/zen_uploads").resolve()
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_FETCH_HOSTS = {"example.com", "httpbin.org"}


def _safe_upload_path(filename: str) -> Path:
    cleaned = secure_filename(filename or "")
    if not cleaned:
        raise ValueError("Invalid filename")
    target = (UPLOAD_ROOT / cleaned).resolve()
    if not target.is_relative_to(UPLOAD_ROOT):
        raise ValueError("Path outside upload directory")
    return target


@app.route("/api/search", methods=["GET"])
def search():
    """Search endpoint used by simulation tests."""
    query = request.args.get("q", "")

    if query.startswith("file:"):
        try:
            target = _safe_upload_path(query.split("file:", 1)[1])
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        if not target.exists():
            return jsonify({"error": "File not found"}), 404
        return jsonify({"result": target.read_text(encoding="utf-8", errors="ignore")})

    if query.startswith(("http://", "https://")):
        parsed = urlparse(query)
        if parsed.hostname not in ALLOWED_FETCH_HOSTS:
            return jsonify({"error": "Host not allowed"}), 400
        response = requests.get(query, timeout=5)
        return jsonify({"content": response.text})

    return f"<h1>Search Results for: {escape(query)}</h1>"


@app.route("/api/admin", methods=["GET"])
def admin_panel():
    """Simple admin simulation endpoint."""
    action = request.args.get("action")
    if action == "delete_user":
        user_id = request.args.get("user_id")
        return jsonify({"status": "User deleted", "user_id": user_id})
    return jsonify({"status": "Admin panel"})


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Upload endpoint with secure filename handling."""
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400
    try:
        target = _safe_upload_path(file.filename or "")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    file.save(target)
    return jsonify({"status": "File uploaded", "path": str(target)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
