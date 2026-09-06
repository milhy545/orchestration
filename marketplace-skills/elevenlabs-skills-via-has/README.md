# ElevenLabs Skills Via HAS

Local `skills` collection for managed devices that should route ElevenLabs text-to-speech
through `mega-orchestrator` and `elevenlabs-mcp` on HAS instead of using a workstation-local
provider API key.

## Install

```bash
npx skills add /home/orchestration/marketplace-skills/elevenlabs-skills-via-has --skill text-to-speech
```

## Current Skills

- `text-to-speech`

## Notes

- This collection is intended for HAS and managed devices in the same orchestration environment.
- The official upstream installer remains the correct path for notebooks and unmanaged machines.
- The collection is a normal `skills` repository layout: each skill lives in its own top-level
  directory with a `SKILL.md`.
