---
name: speak
description: Generate spoken audio for the latest Claude reply through mega-orchestrator and ElevenLabs MCP on HAS.
---

# Speak

Use this skill when the user asks for narration, audio output, or a spoken version of the latest reply.

## Workflow

1. Prefer the latest assistant reply unless the user provided explicit replacement text.
2. Call mega-orchestrator tool `speak_generate` with `agent_family="claude"`.
3. Return the resulting file path and keep the response concise.

## Notes

- Runtime contract: `core/references/runtime-contract.md`
- This skill should not embed provider secrets or call ElevenLabs HTTP directly.
