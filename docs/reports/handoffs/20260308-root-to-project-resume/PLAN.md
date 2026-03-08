# Frozen Plan

## Phase 1: Perplexity HUB Completion

- Treat `perplexity-hub` as the canonical research runtime.
- Replace the previous `research-mcp` runtime path with the new hub in compose, orchestrator routing, and operator-facing docs.
- Keep Perplexity as retrieval provider and allow optional OpenAI synthesis/post-processing.
- Reach deterministic local coverage for the retained hub code and validate end-to-end request flow.

## Phase 2: Vault Secret Delivery Refactor

- Stop injecting active secrets as raw environment variables for retained services.
- Render service secrets as files and pass file paths, not raw secrets, into service startup.
- Update consumers to read `*_FILE` inputs first.
- Prove that secrets are no longer visible in `docker inspect` for migrated services.

## Phase 3: Orchestration-Wide Security Cleanup

- Audit retained active services for secret exposure, command execution risk, logging leaks, and path handling.
- Expand tests and coverage for retained active runtime code.
- Quarantine stale or superseded material into `archive/trash/<timestamp>/`.
- Complete cleanup only after local verification and passing GitHub checks.

## Resume Rule

The next implementation session should continue from the canonical thread:

```bash
cd /home/orchestration
codex resume 019cc917-5880-73a0-a100-fb68342b4f72 -C /home/orchestration
```
