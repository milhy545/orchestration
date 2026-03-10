import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO_ROOT / "docs" / "api" / "public_surface_inventory.json"

BANNED_TERMS = [
    "ZEN Coordinator",
    "Master Control Program",
    "28 MCP tools",
    "7 specialized services",
    "Only exposed port",
    "placeholder service",
    "/home/orchestration/",
]


def _active_doc_paths() -> list[Path]:
    roots = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "SECURITY.md",
    ]
    docs_root = REPO_ROOT / "docs"
    docs = [
        path
        for path in docs_root.rglob("*.md")
        if "archive" not in path.parts and "reports" not in path.parts
    ]
    return roots + docs


def test_inventory_references_existing_docs():
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    for section in ("services", "operator_scripts", "excluded_surfaces"):
        for item in inventory[section]:
            doc_path = REPO_ROOT / item["doc"]
            assert doc_path.exists(), f"Missing doc for {item['id']}: {item['doc']}"
            content = doc_path.read_text(encoding="utf-8")
            for token in item["tokens"]:
                assert token in content, f"Missing token {token!r} in {item['doc']} for {item['id']}"


def test_active_docs_do_not_use_legacy_terms():
    for path in _active_doc_paths():
        content = path.read_text(encoding="utf-8")
        for term in BANNED_TERMS:
            assert term not in content, f"Legacy term {term!r} found in {path}"


def test_mkdocs_config_exists():
    mkdocs_path = REPO_ROOT / "mkdocs.yml"
    assert mkdocs_path.exists(), "mkdocs.yml is missing"


def test_active_docs_are_english_only_for_prose():
    czech_chars = "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"
    for path in _active_doc_paths():
        content = path.read_text(encoding="utf-8")
        assert not any(ch in content for ch in czech_chars), f"Czech text found in {path}"
