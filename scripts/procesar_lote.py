#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para procesar un lote de documentos y extraer solo los .corrections.docx"""
import os
import sys
import requests
import time
from pathlib import Path
import shutil

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_URL = "http://localhost:8001"
EMAIL = "demo@example.com"
PASSWORD = "demo123"
CORRECCIONES_DIR = Path("correcciones")
OUTPUT_DIR = Path("correcciones_finales")

# 1. Login
print("[AUTH] Autenticando...")
resp = requests.post(f"{API_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
resp.raise_for_status()
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("[OK] Token obtenido")

# 2. Obtener proyecto
print("\n[PROJECT] Obteniendo proyecto...")
resp = requests.get(f"{API_URL}/projects", headers=headers)
resp.raise_for_status()
projects = resp.json()
project_id = projects[0]["id"]
print(f"[OK] Proyecto: {projects[0]['name']} ({project_id})")

# 3. Subir documentos (todos a la vez)
docx_files = sorted(CORRECCIONES_DIR.glob("*.docx"))
print(f"\n[UPLOAD] Subiendo {len(docx_files)} documentos...")
files_to_upload = [
    ("files", (f.name, open(f, "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    for f in docx_files
]
resp = requests.post(f"{API_URL}/projects/{project_id}/documents/upload", headers=headers, files=files_to_upload)
for _, (_, f, _) in files_to_upload:
    f.close()  # Close all opened files
resp.raise_for_status()
print(f"[DEBUG] Response status: {resp.status_code}")
print(f"[DEBUG] Response text: {resp.text[:500]}...")
uploaded_docs = resp.json()
print(f"[DEBUG] Response type: {type(uploaded_docs)}")
print(f"[DEBUG] Response length: {len(uploaded_docs)}")
if uploaded_docs:
    print(f"[DEBUG] First doc: {uploaded_docs[0]}")
    print(f"[DEBUG] First doc type: {type(uploaded_docs[0])}")
    print(f"[DEBUG] First doc keys: {uploaded_docs[0].keys() if isinstance(uploaded_docs[0], dict) else 'not a dict'}")
document_ids = [doc["id"] for doc in uploaded_docs]
print(f"[OK] Subidos {len(document_ids)} documentos")

# 4. Crear run con todos los documentos
print(f"\n[RUN] Creando run con {len(document_ids)} documentos...")
resp = requests.post(
    f"{API_URL}/runs",
    headers=headers,
    json={"project_id": project_id, "document_ids": document_ids, "use_ai": True}
)
resp.raise_for_status()
run_id = resp.json()["run_id"]
print(f"[OK] Run creado: {run_id}")

# 5. Monitorear progreso
print("\n[WAIT] Esperando a que complete el procesamiento...")
print("   (Esto puede tardar ~15-20 minutos para 41 documentos con gemini-2.5-pro)")
while True:
    resp = requests.get(f"{API_URL}/runs/{run_id}", headers=headers)
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
        break

    time.sleep(10)

# 6. Descargar solo los .corrections.docx
print(f"\n[DOWNLOAD] Descargando archivos de correcciones...")
resp = requests.get(f"{API_URL}/runs/{run_id}/exports", headers=headers)
resp.raise_for_status()
exports = resp.json()

OUTPUT_DIR.mkdir(exist_ok=True)

corrections_files = [e for e in exports if e["category"] == "log_docx"]
print(f"   Encontrados {len(corrections_files)} archivos de correcciones")

for export in corrections_files:
    filename = export["name"]
    print(f"   Descargando: {filename}...", end=" ")

    resp = requests.get(f"{API_URL}/artifacts/{run_id}/{filename}", headers=headers)
    resp.raise_for_status()

    output_path = OUTPUT_DIR / filename
    with open(output_path, "wb") as f:
        f.write(resp.content)

    print(f"[OK] Guardado en {output_path}")

print(f"\n[DONE] Completado! Archivos guardados en: {OUTPUT_DIR.absolute()}")
print(f"   Total de archivos: {len(list(OUTPUT_DIR.glob('*.docx')))}")
