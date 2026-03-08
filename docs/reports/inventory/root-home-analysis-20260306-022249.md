# Root Home Migration Analysis

Date (UTC): 2026-03-06 02:22:49  
Scope: strict orchestration-only migration from `/root` into `/home/orchestration`

## Summary

The active orchestration repository was already located in `/home/orchestration`.
This migration cleaned up only the orchestration artifacts that were still left in `/root`:

- `/root/archived-mcp-servers-20250723/`
- `/root/perplexity-mcp-setup-prompt.txt`

Both items were moved into:

- `/home/orchestration/archive/migration/root-home-migration-20260306-022249/`

No running services were restarted. No runtime configuration was changed.

## Items Moved

### 1. Archived MCP server bundle

Source:
- `/root/archived-mcp-servers-20250723/`

Destination:
- `/home/orchestration/archive/migration/root-home-migration-20260306-022249/archived-mcp-servers-20250723/`

Contained historical snapshots of:
- `database-mcp`
- `filesystem-mcp`
- `git-mcp`
- `memory-mcp`
- `research-mcp`
- `terminal-mcp`
- `webm-transcriber`

### 2. Historical Perplexity MCP setup prompt

Source:
- `/root/perplexity-mcp-setup-prompt.txt`

Destination:
- `/home/orchestration/archive/migration/root-home-migration-20260306-022249/prompts/perplexity-mcp-setup-prompt.txt`

## Pre-Migration Snapshot

### Source existence

- `archived-mcp-servers-20250723`: present
- `perplexity-mcp-setup-prompt.txt`: present

### Candidate sizes

- `archived-mcp-servers-20250723`: `140K`
- `perplexity-mcp-setup-prompt.txt`: `4.0K`

### Candidate file count

- `archived-mcp-servers-20250723`: `23` files

### Prompt checksum before migration

- `41666bb0f960883cfe46600755ad773db264fa11ccd118864cdbb6abd0f220c9`

### Git status before migration

```text
 M .env.example
 M README.md
 M blackbox_mcp_settings.json
 M docker-compose.vault.yml
 M docker-compose.yml
 M docs/reports/testing/TEST_SUMMARY_UPDATE.md
 M mcp-servers/config-mcp/main.py
 M mcp-servers/config-mcp/tests/test_security.py
 M mcp-servers/database-mcp/main.py
 M mcp-servers/filesystem-mcp/main.py
 M mcp-servers/filesystem-mcp/tests/test_main.py
 M mcp-servers/forai-mcp/main.py
 M mcp-servers/log-mcp/main.py
 M mcp-servers/log-mcp/tests/test_security.py
 M mcp-servers/marketplace-mcp/main.py
 M mcp-servers/memory-mcp/main.py
 M mcp-servers/mqtt-mcp/main.py
 M mcp-servers/research-mcp/main.py
 M mcp-servers/security-mcp/main.py
 M mcp-servers/security-mcp/tests/test_main.py
 M mcp-servers/terminal-mcp/main.py
 M mcp-servers/terminal-mcp/tests/test_main.py
 M mcp-servers/zen-mcp/docker/scripts/healthcheck.py
 M mega_orchestrator/mcp_tooling.py
 M mega_orchestrator/mega_orchestrator_complete.py
 M monitoring/loki/loki-config.yml
 M monitoring/prometheus/prometheus.yml
 M monitoring/promtail/promtail-config.yml
 M tests/unit/orchestration_workflow_test.sh
?? ANTIGRAVITY_CODEX_PROMPT.txt
?? CURRENT_SERVICE_STATUS.md
?? WINDOWS_CODEX_PROMPTS.txt
?? docker-compose.remote-ide.yml
?? docs/manuals/GEMINI_DOC_TRANSLATION_PROMPT.md
?? mcp-servers/mqtt-mcp/tests/
?? mcp_fix_plan.md
?? services/remote-ide-ssh/
```

## Verification

### Copy integrity

- Source file count: `23`
- Destination file count: `23`
- Relative file list diff: clean
- Source archive size: `140K`
- Destination archive size: `140K`
- Prompt source checksum: `41666bb0f960883cfe46600755ad773db264fa11ccd118864cdbb6abd0f220c9`
- Prompt destination checksum: `41666bb0f960883cfe46600755ad773db264fa11ccd118864cdbb6abd0f220c9`

### Post-migration source removal

- `/root/archived-mcp-servers-20250723`: absent
- `/root/perplexity-mcp-setup-prompt.txt`: absent

### Runtime reference check

Search for direct references to the removed root paths under `/home/orchestration` returned no matches:

- `/root/archived-mcp-servers-20250723`
- `/root/perplexity-mcp-setup-prompt.txt`

## Remaining Artifacts In `/root`

The following top-level artifacts still remain in `/root` after the strict migration. They were intentionally left in place because they are either home-directory/tooling state, separate projects, backup archives, or non-orchestration materials.

### Home and tooling state

- `.android/`
- `.antigravity-server/`
- `.cache/`
- `.claude/`
- `.codex/`
- `.config/`
- `.cursor/`
- `.cursor-server/`
- `.docker/`
- `.dotnet/`
- `.elinks/`
- `.gemini/`
- `.gnupg/`
- `.local/`
- `.npm/`
- `.nvm/`
- `.oh-my-zsh/`
- `.pki/`
- `.plandex-home-v2/`
- `.ssh/`
- `.tmux/`
- `.trae-server/`
- `.vscode-server/`
- `.windsurf-server/`
- `venv/`
- `node_modules/`

### Shell and local configuration files

- `.ash_history`
- `.bash_history`
- `.bashrc`
- `.claude.json`
- `.claude.json.backup`
- `.claude.json.backup.1772472573568`
- `.gitconfig`
- `.rnd`
- `.shell_common`
- `.tmux.conf`
- `.wget-hsts`
- `.z`
- `.zcompdump-home-automat-server-5.9`
- `.zcompdump-home-automat-server-5.9.lock/`
- `.zcompdump-home-automat-server-5.9.zwc`
- `.zsh_history`
- `.zshrc`
- `.zshrc.backup.20251112_043204`
- `.zshrc.backup.minipc-unif`
- `.zshrc.backup.omz-unif`

### Separate projects and working directories

- `fei/`
- `llms_config/`
- `oauth_speech_staging/`
- `perplexity-ha-control/`
- `perplexity-ha-integration/`
- `templates/`
- `test-repo/`
- `__pycache__/`
- `bin/`

### Backup archives and retained bundles

- `llms_config.tar.gz`
- `llms_config.tar.gz.1`
- `project_backup.tar.gz`
- `project_data.tar.gz`
- `tailscale.tgz`

### WebDAV project artifacts

- `README_webdav_uploader.md`
- `WebDAV_Uploader_PDF_Guide.md`
- `install_webdav_uploader.sh`
- `requirements_web.txt`
- `test_webdav_uploader.py`
- `webdav_config.env`
- `webdav_uploader.py`
- `webdav_users.db`
- `webdav_web_interface.py`

### Local AI / prompt / doc artifacts

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `COMPLETE_DOCUMENTATION.md`
- `HAS-SERVER-SUMMARY.md`
- `MEMORY_FIX_SUMMARY.txt`
- `claude-cli`
- `claude-server-prompt.txt`
- `claude-status.sh`
- `last-response.md`
- `package-lock.json`
- `package.json`
- `requirements.txt`
- `restore_network.sh`
- `setup-claude-api.sh`
- `system_monitor.sh`
- `test_perplexity_key.py`
- `tmux-autostart.sh`

## Git Status After Migration

```text
 M .env.example
 M README.md
 M blackbox_mcp_settings.json
 M docker-compose.vault.yml
 M docker-compose.yml
 M docs/reports/testing/TEST_SUMMARY_UPDATE.md
 M mcp-servers/config-mcp/main.py
 M mcp-servers/config-mcp/tests/test_security.py
 M mcp-servers/database-mcp/main.py
 M mcp-servers/filesystem-mcp/main.py
 M mcp-servers/filesystem-mcp/tests/test_main.py
 M mcp-servers/forai-mcp/main.py
 M mcp-servers/log-mcp/main.py
 M mcp-servers/log-mcp/tests/test_security.py
 M mcp-servers/marketplace-mcp/main.py
 M mcp-servers/memory-mcp/main.py
 M mcp-servers/mqtt-mcp/main.py
 M mcp-servers/research-mcp/main.py
 M mcp-servers/security-mcp/main.py
 M mcp-servers/security-mcp/tests/test_main.py
 M mcp-servers/terminal-mcp/main.py
 M mcp-servers/terminal-mcp/tests/test_main.py
 M mcp-servers/zen-mcp/docker/scripts/healthcheck.py
 M mega_orchestrator/mcp_tooling.py
 M mega_orchestrator/mega_orchestrator_complete.py
 M monitoring/loki/loki-config.yml
 M monitoring/prometheus/prometheus.yml
 M monitoring/promtail/promtail-config.yml
 M tests/unit/orchestration_workflow_test.sh
?? ANTIGRAVITY_CODEX_PROMPT.txt
?? CURRENT_SERVICE_STATUS.md
?? WINDOWS_CODEX_PROMPTS.txt
?? archive/migration/root-home-migration-20260306-022249/
?? docker-compose.remote-ide.yml
?? docs/manuals/GEMINI_DOC_TRANSLATION_PROMPT.md
?? docs/reports/inventory/
?? mcp-servers/mqtt-mcp/tests/
?? mcp_fix_plan.md
?? services/remote-ide-ssh/
```

## Notes

- The migration was intentionally conservative.
- No attempt was made to fold unrelated `/root` projects into the orchestration repository.
- The moved materials are archived only and must not be treated as active runtime dependencies unless explicitly restored.
