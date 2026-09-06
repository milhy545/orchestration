#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "   Smart Deploy System v3.0 - Zero-Touch Onboarding"
echo "============================================================"

INSTALL_DIR="\$HOME/Develop/Smart-Deploy-System"
mkdir -p "\$INSTALL_DIR"
mkdir -p "\$HOME/.local/bin"

echo "1. Syncing System from HAS..."
rsync -avz HAS:/home/orchestration/Smart-Deploy-System/ "\$INSTALL_DIR/"

echo "2. Setting up Python Environment..."
if [ ! -d "\$INSTALL_DIR/venv" ]; then
    python3 -m venv "\$INSTALL_DIR/venv"
    "\$INSTALL_DIR/venv/bin/pip" install flask flask-cors
fi

echo "3. Creating global symlinks..."
ln -sf "\$INSTALL_DIR/welcome-dashboard/launch.sh" "\$HOME/.local/bin/welcome_dashboard"

echo "4. Onboarding Complete."
echo "   Run 'welcome_dashboard' to start the visual UI."
echo "============================================================"
