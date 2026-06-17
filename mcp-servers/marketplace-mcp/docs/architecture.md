# Marketplace MCP Architecture

## Complete Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Milhy-PC                                       │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   Pi     │  │  Codex   │  │ Gemini   │  │ Claude   │  │ Antigrav │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │              │              │              │              │           │
│       └──────────────┴──────────────┴──────┬───────┴──────────────┘           │
│                                           │                                  │
│                                    ┌──────▼──────┐                          │
│                                    │ mega_orch-  │                          │
│                                    │ estrator()  │ ← MCP tool              │
│                                    └──────┬──────┘                          │
│                                           │                                  │
└───────────────────────────────────────────┼──────────────────────────────────┘
                              ┌─────────────▼─────────────┐
                              │         HAS               │
                              │    (192.168.0.58)         │
                              │                           │
                              │  ┌─────────────────────┐  │
                              │  │  Mega-Orchestrator  │  │
                              │  │  (port 7000)        │  │
                              │  │                     │  │
                              │  │  skills_list        │  │
                              │  │  skills_resolve     │  │
                              │  │  registry_search    │  │
                              │  └──────────┬──────────┘  │
                              │             │             │
                              │  ┌──────────▼──────────┐  │
                              │  │  Marketplace MCP    │  │
                              │  │  (port 7034)        │  │
                              │  │                     │  │
                              │  │  - 92 skills        │  │
                              │  │  - JWT auth         │  │
                              │  └─────────────────────┘  │
                              └───────────────────────────┘
```

## Tools Available via Mega-Orchestrator

| Tool | Description |
|------|-------------|
| `skills_list` | List skills from catalog (filter by tag) |
| `skills_resolve` | Get skill details |
| `registry_search` | List MCP servers |
| `registry_get_server` | Get MCP server details |
| `catalog_validate` | Validate catalog integrity |

## Scripts

| Script | Purpose |
|--------|---------|
| `skill-scanner.py` | Scan skills from Milhy-PC agents |
| `agent-sync.py` | Sync skills between agents via symlinks |
| `sync-catalog-to-has.sh` | Sync catalog to HAS and rebuild container |
| `generate-token.py` | Generate JWT tokens for API access |
| `launch-marketplace.sh` | Start marketplace locally |
| `test-marketplace.sh` | Run test suite |

## Usage

```bash
# Scan skills and sync to HAS
./scripts/sync-catalog-to-has.sh

# Generate token for manual API access
./scripts/generate-token.py market:read

# Run tests
./tests/test-marketplace.sh
```
