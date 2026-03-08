# Root-to-Project Resume Handoff

Date (UTC): 2026-03-08T07:37:19Z

This bundle preserves the current orchestration conversation in a project-visible form without copying Codex's canonical session database into the repository.

## Canonical Resume Target

- Main thread ID: `019cc917-5880-73a0-a100-fb68342b4f72`
- Main thread stored cwd: `/root`
- Main rollout path: `/root/.codex/sessions/2026/03/07/rollout-2026-03-07T16-17-56-019cc917-5880-73a0-a100-fb68342b4f72.jsonl`
- Worker thread ID to ignore for resume: `019ccc43-e923-7023-88c6-e3eac61be3bd`

## Exact Resume Command

```bash
cd /home/orchestration
codex resume 019cc917-5880-73a0-a100-fb68342b4f72 -C /home/orchestration
```

Project-local helper:

```bash
/home/orchestration/scripts/codex-resume-orchestration.sh
```

If using the picker instead of an explicit session ID, use `codex resume --all` because picker output is filtered by cwd by default.

## What This Bundle Contains

- `TRANSCRIPT.md`: sanitized conversation chronology
- `PLAN.md`: frozen implementation plan that was approved before the interruption
- `TODO.md`: actionable next steps for the next Codex continuation
- `STATE.md`: current implementation and verification status
- `WORKTREE.md`: git worktree snapshot captured during the handoff

## Important Boundary

The authoritative Codex session history remains in `/root/.codex`. This repository only stores a sanitized handoff so the project can be resumed from the correct directory without depending on memory of the prior thread state.
