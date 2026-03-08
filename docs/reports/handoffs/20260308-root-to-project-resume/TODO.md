# TODO

- Classify the already-dirty worktree before broad cleanup or deletion.
- Reconcile the final retained `perplexity-hub` implementation shape and remove any duplicate or abandoned variants.
- Finish compose and orchestrator cutover from `research-mcp` to `perplexity-hub`.
- Roll out file-based secret delivery beyond the first migrated service path.
- Replace the current dev-style Vault runtime with the intended retained configuration.
- Run wider local verification for the active stack, not only targeted service tests.
- Prepare the later repo-cleanup pass so archival moves do not trample user-owned dirty changes.
- Only after the above: commit, push, and fix GitHub checks until green.
