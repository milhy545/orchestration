from mega_orchestrator.utils.welcome_service import WelcomeService


def test_welcome_service_updates_agent_and_hw_registries(tmp_path):
    service = WelcomeService(str(tmp_path))

    result = service.welcome(
        agent_name="codex",
        agent_version="1.0",
        current_hw_data={"cpu": "i5-4690K", "ram_gb": 32},
        semantic_context={"items": []},
    )

    assert "Welcome, codex" in result["welcome_markdown"]
    assert result["welcome_json"]["hardware"]["updated"] is True
    assert (tmp_path / "agent_registry.json").is_file()
    assert (tmp_path / "hw_registry.json").is_file()


def test_welcome_service_is_idempotent_for_same_hw(tmp_path):
    service = WelcomeService(str(tmp_path))
    service.welcome(agent_name="codex", current_hw_data={"cpu": "i5-4690K"})

    second = service.welcome(agent_name="codex", current_hw_data={"cpu": "i5-4690K"})

    assert second["welcome_json"]["hardware"]["updated"] is False
    assert second["welcome_json"]["agent"]["welcome_count"] == 2
