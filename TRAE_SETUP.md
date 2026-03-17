# Trae Agent Setup: Low-Resource HAS Development Workflow

Ahoj Trae Agente! Tvým úkolem je nastavit vývojové prostředí pro tento projekt tak, aby **naprosto nulově** zatěžovalo CPU na serveru HAS. Uživatel chce využívat tvé AI schopnosti, ale veškerý výpočetní výkon (indexace, LLM, Language Server) musí běžet na **lokálním stroji**, nikoliv na HAS.

## 🎯 Cíl
Přestat používat "Remote-SSH" plugin (který instaluje `.trae-server` na HAS) a přejít na **SSHFS mount**.

## 🛠️ Postup pro tebe (Trae Agent):

1. **Zkontroluj lokální závislosti:**
   - Ověř, zda je v lokálním systému nainstalován `sshfs`. Pokud ne, upozorni uživatele, ať ho nainstaluje (`sudo apt install sshfs`).

2. **Příprava Mount Pointu:**
   - Vytvoř v domovském adresáři uživatele složku pro připojení: `mkdir -p ~/mnt/has-orchestration`.

3. **Vytvoření Mount skriptu:**
   - Vytvoř v kořeni tohoto repozitáře pomocný skript `dev-mount.sh` s následujícím obsahem:
     ```bash
     #!/bin/bash
     MOUNT_POINT="$HOME/mnt/has-orchestration"
     mkdir -p $MOUNT_POINT
     # Odpojení pokud už existuje
     fusermount -u $MOUNT_POINT 2>/dev/null
     # Připojení přes SSHFS (používá lokální prostředky pro indexaci)
     sshfs HAS:/home/orchestration $MOUNT_POINT -o auto_unmount,reconnect,follow_symlinks
     echo "✅ HAS připojen do $MOUNT_POINT"
     echo "👉 Nyní v Trae otevři SLOŽKU: $MOUNT_POINT"
     ```
   - Nastav mu spustitelnost: `chmod +x dev-mount.sh`.

4. **Instrukce pro indexaci:**
   - Nastav `.vscode/settings.json` (nebo nastavení Trae), aby **indexovalo pouze tento připojený mount point**.
   - Všechna data indexu (Local Index, CKG) se musí ukládat **lokálně** na PC uživatele.

5. **Kontrola HAS:**
   - Spusť `ssh HAS "ps aux | grep trae"` a ujisti se, že na serveru neběží žádný zapomenutý `.trae-server`. Pokud ano, killni ho.

## 🚀 Jak vyvíjet (pro uživatele):
1. Spustíš `./dev-mount.sh`.
2. V Trae dáš "Open Folder" a vybereš `~/mnt/has-orchestration`.
3. Trae si vše zaindexuje u sebe na PC.
4. HAS bude mít klid a ty máš plný výkon AI.
