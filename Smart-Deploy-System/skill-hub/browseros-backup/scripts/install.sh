#!/usr/bin/env bash
# BrowserOS Backup & Restore Installer
set -euo pipefail

INSTALL_DIR="$HOME/.browseros/skills/custom/browseros-backup"
BIN_DIR="$HOME/.local/bin"

echo "Instaluji BrowserOS Backup & Restore n\u00e1stroje..."

# 1. Vytvo\u0159en\u00ed adres\u00e1\u0159\u016f
mkdir -p "$BIN_DIR"
mkdir -p "$INSTALL_DIR"

# 2. Nastaven\u00ed pr\u00e1v pro spu\u0161t\u011bn\u00ed
chmod +x "$INSTALL_DIR/backup.sh" "$INSTALL_DIR/restore.sh"

# 3. Vytvo\u0159en\u00ed symlink\u016f
ln -sf "$INSTALL_DIR/backup.sh" "$BIN_DIR/backup_browseros"
ln -sf "$INSTALL_DIR/restore.sh" "$BIN_DIR/restore_browseros"

echo "Instalace dokon\u010dena."
echo "P\u0159\u00edkazy 'backup_browseros' a 'restore_browseros' jsou nyn\u00ed dostupné glob\u00e1ln\u011b."
echo "Pro n\u00e1pov\u011bdu pou\u017eijte parametr -h nebo --help."
