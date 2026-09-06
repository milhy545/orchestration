---
name: speak
description: Read the latest Gemini reply aloud through mega-orchestrator and ElevenLabs MCP on HAS.
---

# Speak

Use this skill for `/speak`, `read that`, or direct requests for spoken output.

## Workflow

1. Prefer `GEMINI_LAST_REPLY` when it is available.
2. Otherwise use the latest assistant reply or the explicit text provided by the user.
3. Call mega-orchestrator tool `speak_generate` with `agent_family="gemini"`.
4. Return the generated audio path instead of attempting direct HTTP playback.

## Notes

- Core runtime details are in `core/references/runtime-contract.md`.
- This adapter is file-first. Playback is a client concern after generation.
