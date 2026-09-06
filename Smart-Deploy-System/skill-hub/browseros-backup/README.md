# BrowserOS Backup & Restore Tools

This folder contains scripts for backing up and restoring BrowserOS settings and browser profiles.

## Commands

Tools are available globally as:
- `backup_browseros`
- `restore_browseros`

### 1. backup_browseros
Backs up data into encrypted archives in the home directory.

**Usage:**
```bash
backup_browseros [OPTIONS] [PASSWORD]
```

**Options:**
- `--mode [minimal|standard|full]`: Select mode (default: `minimal`).
- `--dry-run`, `-n`: Validate paths without creating an archive.
- `-h`, `--help`: Show help.

### 2. restore_browseros
Restores data from encrypted archives.

**Usage:**
```bash
restore_browseros [OPTIONS] [PASSWORD]
```

**Options:**
- `--mode [minimal|standard|full]`: Select mode (default: `minimal`).
- `-h`, `--help`: Show help.

## Modes
- **minimal**: Only BrowserOS agents and functions (`~/.browseros_minimal.tar.gz.enc`).
- **standard**: Browser profile - history, passwords, bookmarks, etc. (`~/.browseros_standard.tar.gz.enc`).
- **full**: Executes both of the above.

## Installation on another machine
Run the installation script in this folder:
```bash
./install.sh
```
This script ensures script permissions and creates symlinks in `~/.local/bin`.

## Security
Scripts use AES-256-CBC encryption via OpenSSL. Password is required interactively (via `askpass` or terminal) unless provided as an argument or environment variable `BROWSEROS_BACKUP_PASSWORD`.
