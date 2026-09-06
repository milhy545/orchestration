#!/usr/bin/env bash
set -euo pipefail

MODE='minimal'
PASSWORD=''

show_help() {
    echo "Usage: restore_browseros [OPTIONS] [PASSWORD]"
    echo
    echo "Restore BrowserOS settings and browser profiles."
    echo
    echo "Options:"
    echo "  --mode MODE    Select restore mode: minimal, standard, full (default: minimal)"
    echo "  -h, --help     Show this help message and exit"
    echo
    echo "Modes:"
    echo "  minimal        Restore BrowserOS agents and functions"
    echo "  standard       Restore Chrome-like profile (history, passwords, bookmarks, etc.)"
    echo "  full           Execute both minimal and standard restores"
    echo
    echo "Environment Variables:"
    echo "  BROWSEROS_BACKUP_PASSWORD    Password for decryption (overridden by argument)"
}

# Argument parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        *)
            if [[ -z "$PASSWORD" ]]; then
                PASSWORD="$1"
            fi
            shift
            ;;
    esac
done

PASSWORD="${PASSWORD:-${BROWSEROS_BACKUP_PASSWORD:-}}"

askpass_password() {
    local prompt="$1"
    local askpass_bin="${SSH_ASKPASS:-}"
    if [[ -z "$askpass_bin" ]]; then
        askpass_bin="$(command -v ssh-askpass || command -v ksshaskpass || true)"
    fi
    if [[ -n "$askpass_bin" && -x "$askpass_bin" && ( -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ) ]]; then
        "$askpass_bin" "$prompt"
        return 0
    fi
    return 1
}

if [[ -z "$PASSWORD" ]]; then
    if ! PASSWORD="$(askpass_password 'BrowserOS restore decryption password ('$MODE')')" || [[ -z "$PASSWORD" ]]; then
        read -rsp "Enter decryption password: " PASSWORD
        echo >&2
    fi
fi

export BROWSEROS_BACKUP_PASSWORD="$PASSWORD"

# Check if BrowserOS/Chrome is running
if pgrep -x "chrome" > /dev/null || pgrep -f "browser-os" > /dev/null; then
    echo "Error: BrowserOS or Chrome is currently running." >&2
    echo "Please close the browser before performing a restore to avoid database corruption." >&2
    exit 1
fi

# Automatic backup before restore for safety
if [[ "$MODE" != "dry-run" ]]; then
    echo "Creating safety backup before restore..."
    # Using the existing backup script to create a temporary safety backup
    "$(dirname "$0")/backup.sh" --mode "$MODE" "$PASSWORD" --safety-backup
    echo "Safety backup created."
fi

if [[ "$MODE" == "full" ]]; then
    echo "Initiating FULL restore (Minimal + Standard)..."
    "$0" --mode minimal "$PASSWORD"
    "$0" --mode standard "$PASSWORD"
    echo "FULL restore process completed."
    exit 0
fi

BACKUP_FILE=""
if [[ "$MODE" == "minimal" ]]; then
    BACKUP_FILE="$HOME/.browseros_minimal.tar.gz.enc"
elif [[ "$MODE" == "standard" ]]; then
    BACKUP_FILE="$HOME/.browseros_standard.tar.gz.enc"
else
    # Fallback for old backup filename
    if [[ -f "$HOME/.browseros_backup.tar.gz.enc" ]]; then
        BACKUP_FILE="$HOME/.browseros_backup.tar.gz.enc"
    else
        echo "Error: Invalid mode '$MODE' and no legacy backup found." >&2
        exit 1
    fi
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Restore failed: backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

umask 077
cd "$HOME"
echo "Restoring from $BACKUP_FILE..."
if openssl enc -d -aes-256-cbc -salt -pbkdf2 -pass env:BROWSEROS_BACKUP_PASSWORD -in "$BACKUP_FILE" | tar -xz; then
    echo "Restore successful from: $BACKUP_FILE"
else
    echo "Error: Restore failed. Possible incorrect password or corrupted backup file." >&2
    exit 1
fi
unset BROWSEROS_BACKUP_PASSWORD
