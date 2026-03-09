# legacy-skladka

This directory previously contained a large historical scratch archive from
2025-08-23, including old code, docs, dependency manifests, and experiments.

It was removed from the Git repository to eliminate GitHub security noise from
non-runtime historical material and to keep the default branch clean.

The removed archive is preserved outside the repository at:

- `/home/milhy777/orchestration-archives/legacy-skladka-20250823.tar.gz`
- `/home/milhy777/orchestration-archives/zen_coordinator.py.backup`

Reason for externalization:

- historical scratch content was generating Dependabot alerts
- historical Python files were generating CodeQL alerts
- the content is not part of the active orchestration runtime

If this archive is needed again, restore it outside the tracked repository
first and review it before reintroducing any files.
