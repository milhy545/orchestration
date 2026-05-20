import json

from mega_orchestrator.utils.chat_recall import ChatRecall


def test_chat_recall_finds_exact_phrase(tmp_path):
    archive = tmp_path / "2026-04-28-codex-memory-test"
    archive.mkdir()
    (archive / "manifest.json").write_text(
        json.dumps({"title": "Living room media", "kind": "codex"}),
        encoding="utf-8",
    )
    (archive / "transcript.md").write_text(
        "Resili jsme kodi do obyvaku a potom dalsi veci.",
        encoding="utf-8",
    )

    recall = ChatRecall(str(tmp_path))
    result = recall.search("kodi do obyvaku")

    assert result["hit_count"] == 1
    assert result["hits"][0]["match_type"] == "exact"
    assert result["hits"][0]["manifest_path"].endswith("manifest.json")
    assert "kodi do obyvaku" in result["hits"][0]["excerpt"]


def test_chat_recall_audit_counts_archive_files(tmp_path):
    archive = tmp_path / "2026-04-28-codex-memory-test"
    archive.mkdir()
    (archive / "manifest.json").write_text("{}", encoding="utf-8")
    (archive / "transcript.md").write_text("hello", encoding="utf-8")

    audit = ChatRecall(str(tmp_path)).audit()

    assert audit["archive_root_exists"] is True
    assert audit["archive_dirs"] == 1
    assert audit["text_files"] == 1
    assert audit["manifest_files"] == 1
    assert audit["missing_manifest_count"] == 0
