# Branch governance cleanup

## Canonical branch decision

This repository previously had only the `work` branch and no `origin` remote configured.
To align with current Git hosting defaults, `main` is selected as the canonical branch name.

## Performed local actions

1. Created `main` from `work`.
2. Executed validation checks intended for required CI gates:
   - tests: `pytest -q`
   - security: `bandit -r . -q`
3. Fast-forward merged `work` into `main`.
4. Deleted local `work` branch after merge.

## Remote-required follow-up

Because no remote is configured in this clone (`git remote -v` is empty), these operations could not be executed here:

- Set repository default branch on remote.
- Open and merge a remote PR with protected required checks.
- Delete remote `work` branch.
- Apply remote branch protection rules for `main` (required status checks and no direct push).

When a remote is added, apply these settings with your Git host tooling (GitHub UI or `gh` CLI).
