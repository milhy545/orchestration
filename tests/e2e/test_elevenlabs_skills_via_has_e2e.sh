#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_REPO="${REPO_ROOT}/marketplace-skills/elevenlabs-skills-via-has"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required for this E2E test" >&2
  exit 1
fi

cd "${TMP_DIR}"
npx --yes skills add "${SKILLS_REPO}" --skill text-to-speech -a codex -y --copy >/tmp/elevenlabs-skills-via-has-e2e.log 2>&1

TARGET="${TMP_DIR}/.agents/skills/text-to-speech/SKILL.md"
if [[ ! -f "${TARGET}" ]]; then
  echo "Expected installed skill missing: ${TARGET}" >&2
  sed -n '1,200p' /tmp/elevenlabs-skills-via-has-e2e.log >&2 || true
  exit 1
fi

grep -q "speak_generate" "${TARGET}"
echo "PASS: installed ${TARGET}"
