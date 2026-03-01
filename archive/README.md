# Archive Retention Zone

This directory stores historical and non-active project artifacts that should not live in the repository root.

- `backups/` contains retained backup archives.
- `migration/` contains migration-specific historical backups.
- `legacy-config/` contains preserved old config variants and backup files.
- `scratch/` contains non-production workbench material kept for reference.

Nothing in this directory should be treated as an active runtime dependency unless explicitly restored.
