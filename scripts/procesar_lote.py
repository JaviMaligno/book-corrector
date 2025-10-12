#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para procesar un lote de documentos y extraer solo los .corrections.docx

Uso:
    python scripts/procesar_lote.py

Requiere:
    - API corriendo en http://localhost:8001
    - Usuario demo@example.com / demo123
    - Documentos en carpeta correcciones/

Salida:
    - Archivos .corrections.docx en correcciones_finales/
"""
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
CORRECCIONES_DIR = Path("correcciones")
OUTPUT_DIR = Path("correcciones_finales")

def main():
    # 1. Login
    print("[AUTH] Autenticando...")
    resp = requests.post(f"{API_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    resp.raise_for_status()
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Token obtenido\n")

    # 2. Obtener proyecto
    print("[PROJECT] Obteniendo proyecto...")
    resp = requests.get(f"{API_URL}/projects", headers=headers)
    resp.raise_for_status()
    projects = resp.json()
    project_id = projects[0]["id"]
    print(f"[OK] Proyecto: {projects[0]['name']} ({project_id})\n")

    # 3. Subir documentos (todos a la vez)
    docx_files = sorted(CORRECCIONES_DIR.glob("*.docx"))
    print(f"[UPLOAD] Subiendo {len(docx_files)} documentos...")

    if not docx_files:
        print(f"[ERROR] No se encontraron archivos .docx en {CORRECCIONES_DIR.absolute()}")
        return 1

    files_to_upload = [
        ("files", (f.name, open(f, "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
        for f in docx_files
    ]

    try:
        resp = requests.post(
            f"{API_URL}/projects/{project_id}/documents/upload",
            headers=headers,
            files=files_to_upload
        )
        resp.raise_for_status()
        uploaded_docs = resp.json()
        document_ids = [doc["id"] for doc in uploaded_docs]
        print(f"[OK] Subidos {len(document_ids)} documentos\n")
    finally:
        # Close all opened files
        for _, (_, f, _) in files_to_upload:
            f.close()

    # 4. Crear run con todos los documentos
    print(f"[RUN] Creando run con {len(document_ids)} documentos...")
    resp = requests.post(
        f"{API_URL}/runs",
        headers=headers,
        json={"project_id": project_id, "document_ids": document_ids, "use_ai": True}
    )
    resp.raise_for_status()
    run_id = resp.json()["run_id"]
    print(f"[OK] Run creado: {run_id}")
    print(f"     Con rate limiting, esto tomará ~{len(document_ids)*30//60} minutos\n")

    # 5. Monitorear progreso
    print("[MONITOR] Monitoreando progreso...")
    last_processed = -1
    start_time = time.time()

    while True:
        resp = requests.get(f"{API_URL}/runs/{run_id}", headers=headers)
        resp.raise_for_status()
        status_data = resp.json()
        status = status_data["status"]
        processed = status_data.get("processed_documents", 0)
        total = status_data.get("total_documents", 0)

        elapsed = int(time.time() - start_time)
        elapsed_str = f"{elapsed//60}m {elapsed%60}s"

        if processed != last_processed:
            print(f"   [{processed}/{total}] Status: {status} | Tiempo: {elapsed_str}")
            last_processed = processed

        if status == "completed":
            print(f"\n[OK] Procesamiento completado en {elapsed_str}!")
            break
        elif status == "failed":
            print("\n[ERROR] Error en el procesamiento")
            return 1

        time.sleep(10)

    # 6. Descargar correcciones
    print(f"\n[DOWNLOAD] Descargando archivos de correcciones...")
    resp = requests.get(f"{API_URL}/runs/{run_id}/exports", headers=headers)
    resp.raise_for_status()
    exports = resp.json()

    OUTPUT_DIR.mkdir(exist_ok=True)

    corrections_files = [e for e in exports if e["category"] == "log_docx"]
    print(f"   Encontrados {len(corrections_files)} archivos de correcciones")

    for i, export in enumerate(corrections_files, 1):
        filename = export["name"]
        print(f"   [{i}/{len(corrections_files)}] Descargando: {filename}...", end=" ")

        resp = requests.get(f"{API_URL}/artifacts/{run_id}/{filename}", headers=headers)
        resp.raise_for_status()

        output_path = OUTPUT_DIR / filename
        with open(output_path, "wb") as f:
            f.write(resp.content)

        print(f"[OK]")

    print(f"\n[DONE] Completado! Archivos guardados en: {OUTPUT_DIR.absolute()}")
    print(f"   Total de archivos: {len(list(OUTPUT_DIR.glob('*.docx')))}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCEL] Proceso cancelado por el usuario")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] No se puede conectar a la API. ¿Está corriendo en http://localhost:8001?")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
