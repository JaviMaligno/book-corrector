#!/usr/bin/env python
"""Script para reprocesar todos los documentos con el nuevo prompt mejorado"""
import sys
import time
from pathlib import Path

import requests

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_URL = "http://localhost:8001"
EMAIL = "demo@example.com"
PASSWORD = "demo123"
CORRECCIONES_DIR = Path("correcciones")
OUTPUT_DIR = Path("correcciones_finales_v2")

print("=" * 80)
print("REPROCESAMIENTO CON NUEVO PROMPT MEJORADO (Ortografía + Gramática)")
print("=" * 80)

# 1. Login
print("\n[AUTH] Autenticando...")
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
    f.close()
resp.raise_for_status()
uploaded_docs = resp.json()
document_ids = [doc["id"] for doc in uploaded_docs]
print(f"[OK] Subidos {len(document_ids)} documentos\n")

# 4. Crear run con todos los documentos
print(f"[RUN] Creando run con {len(document_ids)} documentos...")
print("     ⚡ Usando NUEVO PROMPT con detección de gramática estructural")
resp = requests.post(
    f"{API_URL}/runs",
    headers=headers,
    json={"project_id": project_id, "document_ids": document_ids, "use_ai": True}
)
resp.raise_for_status()
run_id = resp.json()["run_id"]
print(f"[OK] Run creado: {run_id}")
print(f"     Con rate limiting de 30s entre requests, ~{len(document_ids)*30//60} minutos estimados\n")

# 5. Monitorear progreso
print("[MONITOR] Monitoreando progreso...")
print("=" * 80)
last_processed = -1
start_time = time.time()
while True:
    resp = requests.get(f"{API_URL}/runs/{run_id}", headers=headers)
    resp.raise_for_status()
    status_data = resp.json()
    status = status_data["status"]
    processed = status_data.get("processed_documents", 0)
    total = status_data.get("total_documents", 0)

    if processed != last_processed:
        elapsed = int(time.time() - start_time)
        rate = processed / (elapsed / 60) if elapsed > 0 else 0
        remaining = (total - processed) / rate if rate > 0 else 0
        print(f"   [{processed}/{total}] Status: {status} | Elapsed: {elapsed//60}m{elapsed%60}s | Rate: {rate:.1f} docs/min | ETA: {int(remaining)}min")
        last_processed = processed

    if status == "completed":
        print("\n" + "=" * 80)
        print("[OK] ✅ Procesamiento completado!")
        print("=" * 80)
        break
    elif status == "failed":
        print("\n[ERROR] ❌ Error en el procesamiento")
        break

    time.sleep(10)

# 6. Descargar correcciones
print("\n[DOWNLOAD] Descargando archivos de correcciones...")
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

    print("[OK]")

print(f"\n{'=' * 80}")
print("[DONE] ✅ Completado con NUEVO PROMPT!")
print(f"{'=' * 80}")
print(f"   Archivos guardados en: {OUTPUT_DIR.absolute()}")
print(f"   Total de archivos: {len(list(OUTPUT_DIR.glob('*.docx')))}")
print("\n💡 Mejoras del nuevo prompt:")
print("   • Detección de concordancia (número/género)")
print("   • Tiempos verbales incorrectos")
print("   • Preposiciones incorrectas")
print("   • Construcciones idiomáticas")
print("   • Mezcla de personas gramaticales")
