# BrowserOS Backup & Restore Nástroje

Tato složka obsahuje skripty pro zálohování a obnovu nastavení BrowserOS a profilů prohlížeče.

## Dostupné příkazy

Nástroje jsou dostupné globálně jako:
- `backup_browseros`
- `restore_browseros`

### 1. backup_browseros
Zálohuje data do šifrovaných archivů v domovském adresáři.

**Použití:**
```bash
backup_browseros [OPTIONS] [PASSWORD]
```

**Možnosti:**
- `--mode [minimal|standard|full]`: Výběr režimu (výchozí: `minimal`).
- `--dry-run`, `-n`: Validace cest bez vytvoření archivu.
- `-h`, `--help`: Zobrazí nápovědu.

### 2. restore_browseros
Obnovuje data ze šifrovaných archivů.

**Použití:**
```bash
restore_browseros [OPTIONS] [PASSWORD]
```

**Možnosti:**
- `--mode [minimal|standard|full]`: Výběr režimu (výchozí: `minimal`).
- `-h`, `--help`: Zobrazí nápovědu.

## Režimy (Modes)
- **minimal**: Pouze BrowserOS agenti a funkce (`~/.browseros_minimal.tar.gz.enc`).
- **standard**: Profil prohlížeče - historie, hesla, záložky atd. (`~/.browseros_standard.tar.gz.enc`).
- **full**: Provede oba výše zmíněné kroky.

## Instalace na jiný stroj
V této složce spusťte instalační skript:
```bash
./install.sh
```
Tento skript zajistí nastavení práv a vytvoření symlinků v `~/.local/bin`.

## Bezpečnost
Skripty používají AES-256-CBC šifrování přes OpenSSL. Heslo je vyžadováno interaktivně (přes `askpass` nebo terminál), pokud není předáno jako argument nebo v proměnné prostředí `BROWSEROS_BACKUP_PASSWORD`.
