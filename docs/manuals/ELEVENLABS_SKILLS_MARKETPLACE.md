# ElevenLabs Skills Marketplace

This marketplace now exposes two ElevenLabs installer entries instead of publishing individual
ElevenLabs skills directly in the catalog.

## Installer Entries

### `elevenlabs-skills-installer`

Official upstream installer entry.

Command:

```bash
npx skills add elevenlabs/skills
```

Use this on notebooks and unmanaged machines where direct upstream install is preferred.

### `elevenlabs-skills-via-has`

HAS-backed installer entry.

Command:

```bash
npx skills add /home/orchestration/marketplace-skills/elevenlabs-skills-via-has --skill text-to-speech
```

Use this on HAS and managed devices when ElevenLabs execution should stay centralized on HAS.

## Architecture

- `skills` CLI handles skill installation for the target agent.
- The official installer uses the upstream `elevenlabs/skills` collection directly.
- The HAS-backed installer uses the local collection in
  [marketplace-skills/elevenlabs-skills-via-has](/media/milhy777/Develop/orchestration/marketplace-skills/elevenlabs-skills-via-has).
- The installed `text-to-speech` skill calls `speak_generate` through `mega-orchestrator`.
- `mega-orchestrator` delegates to `elevenlabs-mcp` on HAS.
- The ElevenLabs API key stays in Vault on HAS and is not required on the client machine.

## Current HAS-Backed Skills

- `text-to-speech`

The collection is intentionally minimal and only contains skills that are actually backed by the
current HAS runtime.

## E2E Validation

Run:

```bash
bash tests/e2e/test_elevenlabs_skills_via_has_e2e.sh
```

This validates that:

1. `npx skills add` accepts the local HAS-backed collection path.
2. The `text-to-speech` skill installs for Codex.
3. The installed skill contains the expected `speak_generate` bridge instruction.
