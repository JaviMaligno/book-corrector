#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Monitor batch run and extract corrections when complete"""
import os
import sys
import requests
import time
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_URL = "http://localhost:8001"
EMAIL = "demo@example.com"
PASSWORD = "demo123"
RUN_ID = "7831345a-a7fe-4e11-96bf-f67ab3af852d"
OUTPUT_DIR = Path("correcciones_finales")

# 1. Login
print("[AUTH] Autenticando...")
resp = requests.post(f"{API_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
resp.raise_for_status()
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("[OK] Token obtenido\n")

# 2. Monitor progress
print(f"[MONITOR] Monitoreando run {RUN_ID}...")
while True:
    resp = requests.get(f"{API_URL}/runs/{RUN_ID}", headers=headers)
    resp.raise_for_status()
    status_data = resp.json()
    status = status_data["status"]
    processed = status_data.get("processed_documents", 0)
    total = status_data.get("total_documents", 0)

    print(f"\r   Status: {status} | Procesados: {processed}/{total}", end="", flush=True)

    if status == "completed":
        print("\n[OK] Procesamiento completado!")
        break
    elif status == "failed":
        print("\n[ERROR] Error en el procesamiento")
        sys.exit(1)

    time.sleep(10)

# 3. Download corrections
print(f"\n[DOWNLOAD] Descargando archivos de correcciones...")
resp = requests.get(f"{API_URL}/runs/{RUN_ID}/exports", headers=headers)
resp.raise_for_status()
exports = resp.json()

OUTPUT_DIR.mkdir(exist_ok=True)

corrections_files = [e for e in exports if e["category"] == "log_docx"]
print(f"   Encontrados {len(corrections_files)} archivos de correcciones")

for export in corrections_files:
    filename = export["name"]
    print(f"   Descargando: {filename}...", end=" ")

    resp = requests.get(f"{API_URL}/artifacts/{RUN_ID}/{filename}", headers=headers)
    resp.raise_for_status()

    output_path = OUTPUT_DIR / filename
    with open(output_path, "wb") as f:
        f.write(resp.content)

    print(f"[OK]")

print(f"\n[DONE] Completado! Archivos guardados en: {OUTPUT_DIR.absolute()}")
print(f"   Total de archivos: {len(list(OUTPUT_DIR.glob('*.docx')))}")
