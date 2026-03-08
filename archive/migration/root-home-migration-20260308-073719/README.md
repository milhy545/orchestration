# Root Home Migration Report

Date (UTC): 2026-03-08T07:37:19Z

## Purpose

This migration pass was limited to the current orchestration session handoff problem: make the active orchestration conversation resumable from `/home/orchestration` without relocating Codex's global session database.

## Result

- No additional non-`.codex` orchestration artifacts were moved from `/root` during this pass.
- The current implementation work was already present inside `/home/orchestration`.
- Canonical Codex session state intentionally remains in `/root/.codex`.

## Why Nothing Was Moved

The remaining root-level items discovered during the scan were either:

- global tool state such as `.codex/`, `.gemini/`, shell history, auth, and caches,
- unrelated home-directory content,
- ambiguous historical notes not safely attributable to the active orchestration handoff.

Moving those would have risked breaking other tools or reclassifying unrelated material as active orchestration state.

## Handoff Output Instead

Project-visible handoff material was created under:

- `/home/orchestration/docs/reports/handoffs/20260308-root-to-project-resume/`

That bundle is the project-local view of the current session. The authoritative resume source is still:

- `019cc917-5880-73a0-a100-fb68342b4f72`
- `/root/.codex/sessions/2026/03/07/rollout-2026-03-07T16-17-56-019cc917-5880-73a0-a100-fb68342b4f72.jsonl`
