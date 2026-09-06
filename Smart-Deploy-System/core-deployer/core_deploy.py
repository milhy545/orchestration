#!/usr/bin/env python3
"""
Core Deployer - Smart Deploy System
Handles deployment of Non-AI tools (scripts, binaries, symlinks).
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

def setup_symlink(src, dest):
    src_path = Path(src).expanduser().absolute()
    dest_path = Path(dest).expanduser().absolute()
    
    if not src_path.exists():
        print(f"Error: Source {src_path} does not exist.")
        return False
        
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    if dest_path.is_symlink() or dest_path.exists():
        print(f"Removing existing {dest_path}")
        dest_path.unlink()
        
    print(f"Creating symlink: {dest_path} -> {src_path}")
    dest_path.symlink_to(src_path)
    return True

def main():
    parser = argparse.ArgumentParser(description="Smart Deploy Core Deployer")
    parser.add_argument("action", choices=["install", "list"], help="Action to perform")
    parser.add_argument("--src", help="Source script/binary path")
    parser.add_argument("--name", help="Command name (alias)")
    
    args = parser.parse_args()
    
    bin_dir = Path.home() / ".local/bin"
    
    if args.action == "install":
        if not args.src or not args.name:
            print("Error: --src and --name are required for install.")
            sys.exit(1)
            
        success = setup_symlink(args.src, bin_dir / args.name)
        if success:
            print(f"Successfully installed {args.name}")
    
    elif args.action == "list":
        print(f"Current deployments in {bin_dir}:")
        if bin_dir.exists():
            for item in bin_dir.iterdir():
                if item.is_symlink():
                    print(f"  {item.name} -> {item.readlink()}")

if __name__ == "__main__":
    main()
