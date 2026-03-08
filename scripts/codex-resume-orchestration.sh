#!/usr/bin/env bash
set -euo pipefail

cd /home/orchestration
exec codex resume 019cc917-5880-73a0-a100-fb68342b4f72 -C /home/orchestration "$@"
