# Sanitized Transcript

## Conversation Summary

1. The session started from `/root`, but the active orchestration repository work happened in `/home/orchestration`.
2. `mega-orchestrator` was tested and confirmed healthy. The issue reported by Gemini was traced to wrong MCP connection behavior rather than an outage.
3. `Perplexity HUB` and `research-mcp` were analyzed. The runtime was found to be `research-mcp`, while `Perplexity HUB` existed as a Vault/UI alias rather than a standalone service.
4. A Perplexity API key exposure path was identified: secrets were being injected into container environment variables and were visible via `docker inspect`.
5. A detailed implementation plan was drafted to:
   - finish `Perplexity HUB`,
   - refactor Vault secret delivery,
   - perform a larger orchestration-wide security cleanup.
6. A first implementation slice was completed in `/home/orchestration`, including:
   - creation of a standalone `mcp-servers/perplexity-hub/`,
   - partial compose/orchestrator rewiring,
   - partial file-based secret delivery support for that service,
   - local targeted tests.
7. The user then noticed that the chat had been running with `cwd=/root` and requested a handoff so the next Codex CLI run can continue from `/home/orchestration` with the correct resume target.

## Key Findings Preserved

- Canonical project path: `/home/orchestration`
- Canonical resume thread: `019cc917-5880-73a0-a100-fb68342b4f72`
- Worker thread not to use as resume target: `019ccc43-e923-7023-88c6-e3eac61be3bd`
- Canonical session storage is global under `/root/.codex`, not repo-local
- Resume from project directory requires `-C /home/orchestration`

## Security-Relevant Points

- The previous secret delivery path exposed secrets in container env.
- The required direction is file-based secret delivery rather than raw env injection.
- No raw transcript, secret dump, or `.codex` database copy is stored in this repository handoff.
