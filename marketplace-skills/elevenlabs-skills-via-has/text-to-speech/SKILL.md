---
name: text-to-speech
description: Generate speech through mega-orchestrator and elevenlabs-mcp on HAS without storing the ElevenLabs API key on the local machine.
---

# Text-to-Speech Via HAS

Use this skill when the user wants spoken output and the environment should route execution
through HAS instead of calling ElevenLabs directly from the workstation.

## Goals

- Keep the ElevenLabs API key centralized in Vault on HAS.
- Generate audio through `mega-orchestrator` and `elevenlabs-mcp`.
- Return the generated audio file path or playback result instead of exposing provider secrets.

## Workflow

1. Choose the source text.
2. Prefer the latest assistant reply when the user says `read that` or asks to speak the previous answer.
3. Call the `speak_generate` tool through `mega-orchestrator`.
4. Pass `agent_family` for the current agent when that context exists.
5. Return the generated `output_path` and a short playback hint.

## Constraints

- Do not call the ElevenLabs HTTP API directly from the local machine.
- Do not ask the user to store an ElevenLabs API key on the client machine.
- Keep code blocks, markup noise, and shell transcripts out of the spoken text when possible.

## Example

If the user says `read that aloud`, send the latest relevant reply text to `speak_generate`
and return the resulting audio file location.
