#!/usr/bin/env python3
"""
sync_to_wsl.py — Copy aerothon_sim files from Windows to WSL2 home.
Run this FROM WINDOWS PowerShell or from WSL2 itself.

From WSL2:
  python3 /mnt/c/Users/Jena/.gemini/antigravity-ide/scratch/drone-sim/sync_to_wsl.py

This copies all .py files from the Windows scratch/drone-sim/aerothon_sim
to ~/aerothon_sim in your WSL2 home directory.
"""
import os
import shutil

src_dir = "/mnt/c/Users/Jena/.gemini/antigravity-ide/scratch/drone-sim/aerothon_sim"
dst_dir = os.path.expanduser("~/aerothon_sim")

os.makedirs(dst_dir, exist_ok=True)

files = [f for f in os.listdir(src_dir) if f.endswith(".py")]
for f in files:
    src = os.path.join(src_dir, f)
    dst = os.path.join(dst_dir, f)
    shutil.copy2(src, dst)
    print(f"  ✓ {f}")

print(f"\nSynced {len(files)} files to {dst_dir}")
