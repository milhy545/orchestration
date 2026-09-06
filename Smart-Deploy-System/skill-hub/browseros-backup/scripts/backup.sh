#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
MODE='minimal'
PASSWORD=''

show_help() {
    echo "Usage: backup_browseros [OPTIONS] [PASSWORD]"
    echo
    echo "Backup BrowserOS settings and browser profiles."
    echo
    echo "Options:"
    echo "  --mode MODE    Select backup mode: minimal, standard, full (default: minimal)"
    echo "  --dry-run, -n  Validate paths without creating an archive"
    echo "  -h, --help     Show this help message and exit"
    echo
    echo "Modes:"
    echo "  minimal        Only BrowserOS agents and functions"
    echo "  standard       Chrome-like profile (history, passwords, bookmarks, etc.)"
    echo "  full           Execute both minimal and standard backups"
    echo
    echo "Environment Variables:"
    echo "  BROWSEROS_BACKUP_PASSWORD    Password for encryption (overridden by argument)"
}

IS_SAFETY=0
# Argument parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        --safety-backup)
            IS_SAFETY=1
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        --dry-run|-n)
            DRY_RUN=1
            shift
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

EXT_ID="${BROWSEROS_EXTENSION_ID:-bflpfmnmnokmjhmgnolecpppdbdophmk}"
PROFILE_DIR="${BROWSEROS_PROFILE_DIR:-$HOME/.config/browser-os/Default}"
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

if [[ -z "$PASSWORD" && "$DRY_RUN" -eq 0 ]]; then
    if ! PASSWORD="$(askpass_password 'BrowserOS backup encryption password ('$MODE')')" || [[ -z "$PASSWORD" ]]; then
        read -rsp "Enter encryption password: " PASSWORD
        echo >&2
    fi
fi

export BROWSEROS_BACKUP_PASSWORD="$PASSWORD"

if [[ "$MODE" == "full" ]]; then
    echo "Initiating FULL backup (Minimal + Standard)..."
    EXTRA_ARGS=""
    [[ "$DRY_RUN" -eq 1 ]] && EXTRA_ARGS="--dry-run"
    "$0" --mode minimal "$PASSWORD" $EXTRA_ARGS
    "$0" --mode standard "$PASSWORD" $EXTRA_ARGS
    echo "FULL backup process completed."
    exit 0
fi

BACKUP_FILE=""
TAR_OPTS=()

if [[ "$MODE" == "minimal" ]]; then
    echo "Mode: MINIMAL (BrowserOS agents/functions)"
    BACKUP_FILE="$HOME/.browseros_minimal.tar.gz.enc"
    TARGET_DIRS=(
        "$PROFILE_DIR/Local Extension Settings/$EXT_ID"
        "$PROFILE_DIR/IndexedDB/chrome-extension_${EXT_ID}_0.indexeddb.blob"
        "$PROFILE_DIR/IndexedDB/chrome-extension_${EXT_ID}_0.indexeddb.leveldb"
    )
elif [[ "$MODE" == "standard" ]]; then
    echo "Mode: STANDARD (Browser/Chrome settings)"
    BACKUP_FILE="$HOME/.browseros_standard.tar.gz.enc"
    TAR_OPTS+=("--exclude=Local Extension Settings/$EXT_ID")
    TAR_OPTS+=("--exclude=IndexedDB/chrome-extension_${EXT_ID}_0.indexeddb.blob")
    TAR_OPTS+=("--exclude=IndexedDB/chrome-extension_${EXT_ID}_0.indexeddb.leveldb")
    
    TARGET_DIRS=(
        "$PROFILE_DIR/Local Extension Settings"
        "$PROFILE_DIR/Extensions"
        "$PROFILE_DIR/IndexedDB"
        "$PROFILE_DIR/Local Storage"
        "$PROFILE_DIR/Preferences"
        "$PROFILE_DIR/Secure Preferences"
        "$PROFILE_DIR/Bookmarks"
        "$PROFILE_DIR/History"
        "$PROFILE_DIR/Login Data"
        "$PROFILE_DIR/Cookies"
        "$PROFILE_DIR/Web Data"
    )
else
    echo "Error: Invalid mode '$MODE'" >&2
    exit 1
fi

EXISTING_TARGETS=()
for path in "${TARGET_DIRS[@]}"; do
    if [[ -e "$path" ]]; then
        EXISTING_TARGETS+=("${path#$HOME/}")
    else
        echo "Warning: path not found, skipping: $path" >&2
    fi
done

if [[ ${#EXISTING_TARGETS[@]} -eq 0 ]]; then
    echo "Backup failed: no valid data paths found for mode '$MODE'" >&2
    exit 1
fi

cd "$HOME"

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Dry-run for $MODE: validating paths. Output would be $BACKUP_FILE"
    tar -czf /dev/null "${TAR_OPTS[@]}" -- "${EXISTING_TARGETS[@]}"
    echo "Dry-run successful."
    exit 0
fi

umask 077
tar -cz "${TAR_OPTS[@]}" -- "${EXISTING_TARGETS[@]}"     | openssl enc -aes-256-cbc -salt -pbkdf2 -pass env:BROWSEROS_BACKUP_PASSWORD -out "$BACKUP_FILE"

echo "Backup successful: $BACKUP_FILE (Mode: $MODE)"
unset BROWSEROS_BACKUP_PASSWORD
t "$BACKUP_FILE"

echo "Backup successful: $BACKUP_FILE (Mode: $MODE)"
unset BROWSEROS_BACKUP_PASSWORD
