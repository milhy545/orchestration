#!/usr/bin/env python3
"""
Welcome Dashboard - Smart Deploy System
Intelligent Sync & Centralized Dashboard.
"""
import os
import sys
import socket
import argparse
from pathlib import Path

# Add bridge to path
sys.path.append(str(Path(__file__).parent.parent / "bridge"))
from sync_engine import SyncEngine

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def run_sync_wizard(engine):
    print("\n[🛡️  Sync Wizard]")
    status = engine.check_status()
    for filename, state in status.items():
        if state == "SYNCED":
            print(f"  ✅ {filename:15} : Synchronizováno")
        elif state == "REMOTE_ONLY":
            print(f"  📥 {filename:15} : Chybí lokálně (Stahuji z HAS...)")
            engine.pull_from_has(filename)
        elif state == "LOCAL_ONLY":
            print(f"  📤 {filename:15} : Chybí na HAS")
            choice = input(f"     Chcete nahrát {filename} na HAS jako nový standard? (y/n): ")
            if choice.lower() == 'y':
                engine.push_to_has(filename)
        elif state == "OUT_OF_SYNC":
            print(f"  ⚠️  {filename:15} : Rozdíl nalezen")
            print("     1. Pull z HAS (Přepsat lokální)")
            print("     2. Push na HAS (Aktualizovat Source of Truth)")
            print("     3. Přeskočit")
            choice = input("     Vaše volba (1/2/3): ")
            if choice == '1':
                engine.pull_from_has(filename)
            elif choice == '2':
                engine.push_to_has(filename)

def show_dashboard():
    hostname = socket.gethostname()
    ip = get_ip()
    engine = SyncEngine()
    
    print("="*70)
    print(f"  J.A.R.V.I.S. Ecosystem - Welcome to {hostname}")
    print(f"  SYSTEM: Smart Deploy v2.0 (Source of Truth: HAS)")
    print("="*70)
    print(f"  Status: ONLINE")
    print(f"  Local IP: {ip}")
    print(f"  Network Priority: 1. LAN (2222), 2. Tailscale (22)")
    print("-" * 70)
    
    # Run Sync Check
    run_sync_wizard(engine)
    
    print("-" * 70)
    hub_path = Path("~/Develop/Smart-Deploy-System/skill-hub").expanduser()
    print("  Available Skills in Local HUB:")
    if hub_path.exists():
        for skill in hub_path.iterdir():
            if skill.is_dir():
                print(f"    [ ] {skill.name}")
    
    print("-" * 70)
    print("  Core Tools (Local Status):")
    bin_dir = Path.home() / ".local/bin"
    tools_to_check = ["backup_browseros", "restore_browseros", "vibe", "zed", "welcome_dashboard"]
    if bin_dir.exists():
        for tool in tools_to_check:
            status = "INSTALLED" if (bin_dir / tool).exists() else "MISSING"
            print(f"    {tool:20} : {status}")
    
    print("="*70)

if __name__ == "__main__":
    show_dashboard()
