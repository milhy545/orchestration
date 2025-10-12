#!/bin/bash
# Backup script for orchestrace databases
DATE=$(date +%Y%m%d_%H%M)
BACKUP_DIR="/home/orchestration/data/backups"
DB_DIR="/home/orchestration/data/databases"

echo "Starting database backup at $(date)"

# Použití 'sqlite3 .backup' pro atomické a bezpečné zálohování
# Tím se zabrání poškození zálohy, pokud do databáze probíhá zápis.
sqlite3 ${DB_DIR}/unified_memory_forai.db ".backup '${BACKUP_DIR}/unified_memory_forai_${DATE}.db'"
sqlite3 ${DB_DIR}/cldmemory.db ".backup '${BACKUP_DIR}/cldmemory_${DATE}.db'"

echo "Databases backup finished."
echo "Listing recent backups in ${BACKUP_DIR}:"
ls -lath ${BACKUP_DIR} | head -n 5
