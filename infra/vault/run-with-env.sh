#!/bin/sh
set -eu

if [ "$#" -lt 2 ]; then
  echo "Usage: run-with-env.sh <env-file> <command> [args...]" >&2
  exit 64
fi

ENV_FILE="$1"
shift

if [ ! -f "$ENV_FILE" ]; then
  echo "Vault runtime env file missing: $ENV_FILE" >&2
  exit 66
fi

set -a
# shellcheck source=/dev/null
. "$ENV_FILE"
set +a

exec "$@"
