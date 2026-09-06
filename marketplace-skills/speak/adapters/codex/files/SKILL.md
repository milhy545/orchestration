---
name: speak
description: Generate spoken audio for the latest or supplied response through mega-orchestrator and ElevenLabs MCP on HAS.
---

# Speak

Use this skill when the user asks to read a reply aloud, generate narration, or turn a response into speech.

## Workflow

1. Choose the source text.
2. Prefer the latest assistant reply when the user says `read that` or `/speak`.
3. Call mega-orchestrator tool `speak_generate` with `agent_family="codex"`.
4. Return the generated `output_path` and a short playback hint.

## Notes

- The runtime contract is in `core/references/runtime-contract.md`.
- Do not call ElevenLabs HTTP directly from the skill.
- Keep code blocks and noisy markdown out of the spoken text when possible.
