# Archive Retention Zone

This directory stores historical and non-active project artifacts that should not live in the repository root.

- `backups/` contains retained backup archives.
- `migration/` contains migration-specific historical backups.
- `legacy-config/` contains preserved old config variants and backup files.
- `scratch/` contains non-production workbench material kept for reference.

Nothing in this directory should be treated as an active runtime dependency unless explicitly restored.

## Retention Rules

- Keep runtime-active files out of this tree.
- Prefer descriptive names that include domain and timestamp where possible.
- Backups should follow `*-backup-YYYYMMDD-HHMMSS.*` when created going forward.
- Migration snapshots should follow `*-migration-backup-YYYYMMDD-HHMMSS.*` when created going forward.
- Legacy configs should be preserved here only when they are no longer the active source of truth.
- Scratch material belongs here only if it is intentionally retained for reference.
