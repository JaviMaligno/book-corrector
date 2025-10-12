# Plan de Implementación: Procesamiento en Lote desde Frontend

## Análisis de la API Actual

### ✅ Funcionalidad Existente

El backend **ya tiene toda la funcionalidad necesaria** para procesamiento en lote desde el frontend:

#### 1. **Upload Multiple Documents** ✅
```
POST /projects/{project_id}/documents/upload
Content-Type: multipart/form-data

Body: files[] (array de archivos)
Response: [{ id, name, path, ... }]
```
- ✅ Soporta múltiples archivos en un solo request
- ✅ Retorna lista de document IDs
- ✅ Maneja duplicados con sufijos automáticos

#### 2. **Create Batch Run** ✅
```
POST /runs
Content-Type: application/json

Body: {
  project_id: string,
  document_ids: string[],  // Array de IDs
  use_ai: boolean
}

Response: {
  run_id: string,
  accepted_documents: string[],
  queued: number
}
```
- ✅ Acepta múltiples document_ids en un solo run
- ✅ Encola todos en el scheduler con fair-share
- ✅ Respeta límites de plan (free/premium)

#### 3. **Monitor Progress** ✅
```
GET /runs/{run_id}

Response: {
  run_id: string,
  status: "queued" | "processing" | "completed" | "failed",
  processed_documents: number,
  total_documents: number
}
```
- ✅ Retorna progreso en tiempo real
- ✅ Polling cada 5-10s desde frontend

#### 4. **List Exports** ✅
```
GET /runs/{run_id}/exports

Response: [{
  id: string,
  kind: "docx" | "jsonl" | "csv" | "md",
  name: string,
  category: "report_docx" | "corrected" | "log_jsonl" | "changelog_csv" | "summary_md",
  size: number
}]
```
- ✅ Lista todos los archivos generados
- ✅ Categoriza por tipo (corrections, corrected, logs, etc.)
- ✅ Incluye tamaño de archivo

#### 5. **Download Exports** ✅
```
GET /runs/{run_id}/exports/{export_id}/download
GET /artifacts/{run_id}/{filename}
```
- ✅ Descarga individual por export_id
- ✅ Descarga por filename (legacy, para compatibilidad)

#### 6. **Bulk Download Options** ✅
```
GET /runs/{run_id}/changelog.csv       # CSV agregado de todas las correcciones
GET /runs/{run_id}/summary.md          # Carta editorial/resumen
GET /runs/{run_id}/exports/csv         # CSV on-the-fly si no existe persistente
```
- ✅ Opciones de descarga agregada
- ✅ Formato CSV para análisis en Excel/Sheets

---

## Frontend: Flujo de Procesamiento en Lote

### Wireframe / UX Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Proyecto: "Mi Libro - Capítulos 48-88"                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [📁 Subir Documentos]  [⚙️ Configuración]                 │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Arrastra archivos aquí o haz clic para seleccionar  │ │
│  │                                                       │ │
│  │  📄 capitulo_48.docx (45 KB)            [×]          │ │
│  │  📄 capitulo_49.docx (47 KB)            [×]          │ │
│  │  📄 capitulo_50.docx (44 KB)            [×]          │ │
│  │  ...                                                  │ │
│  │  📄 capitulo_88.docx (48 KB)            [×]          │ │
│  │                                                       │ │
│  │  Total: 41 archivos (1.8 MB)                         │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Opciones:                                                  │
│  ☑ Usar IA (Gemini/Azure GPT-5)                            │
│  ☐ Solo heurísticas locales                                │
│                                                             │
│  [ Cancelar ]                    [🚀 Iniciar Corrección]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

                         ↓ (Usuario hace clic)

┌─────────────────────────────────────────────────────────────┐
│ Procesamiento en Curso                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Run ID: 569ac45c-6c47-46d1-a285-cce6e5ed0386             │
│                                                             │
│  ████████████████████░░░░░░░░  15 / 41 documentos          │
│                                                             │
│  Estado: Procesando                                         │
│  Tiempo transcurrido: 8m 32s                                │
│  Tiempo estimado restante: ~13 minutos                      │
│                                                             │
│  Últimos procesados:                                        │
│  ✅ capitulo_48.docx - 12 correcciones                      │
│  ✅ capitulo_49.docx - 8 correcciones                       │
│  ✅ capitulo_50.docx - 15 correcciones                      │
│  🔄 capitulo_51.docx - Procesando...                        │
│                                                             │
│  [ Cancelar Proceso ]                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

                         ↓ (Cuando completa)

┌─────────────────────────────────────────────────────────────┐
│ ✅ Procesamiento Completado                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Total procesados: 41 documentos                            │
│  Total correcciones: 487                                    │
│  Tiempo total: 21m 45s                                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Descargas Disponibles                               │   │
│  │                                                     │   │
│  │  📊 Reportes de Correcciones                        │   │
│  │     📄 capitulo_48.corrections.docx    [⬇]         │   │
│  │     📄 capitulo_49.corrections.docx    [⬇]         │   │
│  │     ...                                             │   │
│  │     [📦 Descargar todos (ZIP)]                      │   │
│  │                                                     │   │
│  │  📝 Documentos Corregidos                           │   │
│  │     📄 capitulo_48.corrected.docx      [⬇]         │   │
│  │     📄 capitulo_49.corrected.docx      [⬇]         │   │
│  │     ...                                             │   │
│  │     [📦 Descargar todos (ZIP)]                      │   │
│  │                                                     │   │
│  │  📈 Resumen Consolidado                             │   │
│  │     📊 changelog_completo.csv          [⬇]         │   │
│  │     📋 carta_editorial.md              [⬇]         │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [ Volver a Proyectos ]      [🔄 Nueva Corrección]         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementación Frontend

### Tecnologías Recomendadas
- **Framework**: React/Vue/Svelte (según preferencia)
- **Upload**: `react-dropzone` o nativo `<input type="file" multiple>`
- **HTTP Client**: `axios` o `fetch`
- **State Management**: Context API / Redux / Zustand
- **Progress Tracking**: Polling con `setInterval` o WebSockets (futuro)

### Componentes Clave

#### 1. `BatchUploadForm.tsx`
```typescript
interface Props {
  projectId: string;
  onUploadComplete: (documentIds: string[]) => void;
}

// Features:
// - Drag & drop zone
// - File list preview con tamaño
// - Botón "Eliminar" por archivo
// - Validación: solo .docx, max 50 archivos
// - Progress bar durante upload
```

#### 2. `BatchProcessingView.tsx`
```typescript
interface Props {
  runId: string;
}

// Features:
// - Polling cada 5s para actualizar status
// - Progress bar con porcentaje
// - Lista de documentos procesados/pendientes
// - Estimación de tiempo restante
// - Botón cancelar (opcional, requiere backend endpoint)
```

#### 3. `ExportsDownloadPanel.tsx`
```typescript
interface Props {
  runId: string;
  exports: ExportInfo[];
}

// Features:
// - Agrupación por categoría (corrections, corrected, logs)
// - Botón individual de descarga
// - Botón "Descargar todos" (genera ZIP en frontend)
// - Preview de tamaño total
```

### Código de Ejemplo

```typescript
// services/batchProcessing.ts
export class BatchProcessingService {
  private apiUrl = 'http://localhost:8001';
  private token: string;

  async uploadDocuments(
    projectId: string,
    files: File[]
  ): Promise<Document[]> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const response = await fetch(
      `${this.apiUrl}/projects/${projectId}/documents/upload`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${this.token}` },
        body: formData
      }
    );

    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  }

  async createBatchRun(
    projectId: string,
    documentIds: string[],
    useAI: boolean = true
  ): Promise<{ run_id: string }> {
    const response = await fetch(`${this.apiUrl}/runs`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        project_id: projectId,
        document_ids: documentIds,
        use_ai: useAI
      })
    });

    if (!response.ok) throw new Error('Run creation failed');
    return response.json();
  }

  async pollRunStatus(runId: string): Promise<RunStatus> {
    const response = await fetch(`${this.apiUrl}/runs/${runId}`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });

    if (!response.ok) throw new Error('Status fetch failed');
    return response.json();
  }

  async listExports(runId: string): Promise<ExportInfo[]> {
    const response = await fetch(`${this.apiUrl}/runs/${runId}/exports`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });

    if (!response.ok) throw new Error('Exports fetch failed');
    return response.json();
  }

  async downloadExport(runId: string, filename: string): Promise<Blob> {
    const response = await fetch(
      `${this.apiUrl}/artifacts/${runId}/${filename}`,
      { headers: { 'Authorization': `Bearer ${this.token}` } }
    );

    if (!response.ok) throw new Error('Download failed');
    return response.blob();
  }

  // Utility: Download all corrections as ZIP
  async downloadAllCorrectionsAsZip(runId: string): Promise<void> {
    const exports = await this.listExports(runId);
    const corrections = exports.filter(e => e.category === 'report_docx');

    // Use JSZip library
    const zip = new JSZip();

    for (const exp of corrections) {
      const blob = await this.downloadExport(runId, exp.name);
      zip.file(exp.name, blob);
    }

    const content = await zip.generateAsync({ type: 'blob' });
    saveAs(content, `correcciones_${runId}.zip`);
  }
}
```

### Hook de React para Polling

```typescript
// hooks/useRunProgress.ts
export function useRunProgress(runId: string | null) {
  const [status, setStatus] = useState<RunStatus | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!runId) return;

    const interval = setInterval(async () => {
      try {
        const service = new BatchProcessingService();
        const newStatus = await service.pollRunStatus(runId);
        setStatus(newStatus);

        // Stop polling when completed/failed
        if (['completed', 'failed'].includes(newStatus.status)) {
          clearInterval(interval);
        }
      } catch (err) {
        setError(err as Error);
        clearInterval(interval);
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [runId]);

  return { status, error };
}
```

---

## Backend: Mejoras Opcionales

### 1. Endpoint de Cancelación (Opcional)
```python
# server/routes_runs.py

@router.post("/{run_id}/cancel")
def cancel_run(
    run_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user)
):
    """Cancel a running batch process"""
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")

    # Mark all queued/processing documents as cancelled
    rdocs = session.exec(
        select(RunDocument)
        .where(RunDocument.run_id == run_id)
        .where(RunDocument.status.in_([
            RunDocumentStatus.queued,
            RunDocumentStatus.processing
        ]))
    ).all()

    for rd in rdocs:
        rd.status = RunDocumentStatus.failed
        rd.last_error = "Cancelled by user"
        session.add(rd)

    run.status = RunStatus.failed
    session.add(run)
    session.commit()

    # Remove from scheduler queue
    get_scheduler().cancel_run(run_id)

    return {"message": "Run cancelled", "cancelled_documents": len(rdocs)}
```

**Prioridad**: ⭐⭐ (Nice to have, no crítico)

### 2. WebSockets para Progress Updates (Opcional)
```python
# server/websockets.py

from fastapi import WebSocket

@app.websocket("/ws/runs/{run_id}")
async def run_progress_websocket(websocket: WebSocket, run_id: str):
    """Real-time progress updates via WebSocket"""
    await websocket.accept()

    while True:
        # Get current status
        with session_scope() as session:
            run = session.get(Run, run_id)
            if not run:
                await websocket.send_json({"error": "Run not found"})
                break

            rdocs = session.exec(
                select(RunDocument).where(RunDocument.run_id == run_id)
            ).all()

            status = {
                "run_id": run_id,
                "status": run.status.value,
                "processed": len([r for r in rdocs if r.status == RunDocumentStatus.completed]),
                "total": len(rdocs),
                "documents": [
                    {
                        "id": rd.document_id,
                        "status": rd.status.value,
                        "error": rd.last_error
                    } for rd in rdocs
                ]
            }

            await websocket.send_json(status)

            if run.status in [RunStatus.completed, RunStatus.failed]:
                break

        await asyncio.sleep(2)  # Update every 2 seconds
```

**Prioridad**: ⭐ (Opcional, polling funciona bien)

### 3. Bulk ZIP Download Endpoint (Recomendado)
```python
# server/routes_runs.py

@router.get("/{run_id}/exports/corrections.zip")
def download_all_corrections_zip(
    run_id: str,
    session: Session = Depends(get_session),
    current: User = Depends(get_current_user)
):
    """Download all .corrections.docx files as a ZIP"""
    import zipfile
    from io import BytesIO

    exps = session.exec(select(Export).where(Export.run_id == run_id)).all()
    correction_files = [
        e for e in exps
        if e.path.endswith('.corrections.docx')
    ]

    if not correction_files:
        raise HTTPException(status_code=404, detail="No corrections found")

    # Create ZIP in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for exp in correction_files:
            if os.path.exists(exp.path):
                zip_file.write(exp.path, os.path.basename(exp.path))

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=correcciones_{run_id}.zip"
        }
    )
```

**Prioridad**: ⭐⭐⭐ (Muy recomendado para UX)

---

## Checklist de Implementación

### Backend (Mejoras Opcionales)
- [ ] ⭐⭐⭐ Endpoint `/runs/{run_id}/exports/corrections.zip` (ZIP download)
- [ ] ⭐⭐⭐ Endpoint `/runs/{run_id}/exports/corrected.zip` (corrected docs ZIP)
- [ ] ⭐⭐ Endpoint `/runs/{run_id}/cancel` (cancel running batch)
- [ ] ⭐ WebSocket `/ws/runs/{run_id}` (real-time updates)

### Frontend (Necesario)
- [ ] ⭐⭐⭐ `BatchUploadForm` component (drag & drop, multiple files)
- [ ] ⭐⭐⭐ `BatchProcessingView` component (progress tracking)
- [ ] ⭐⭐⭐ `ExportsDownloadPanel` component (download UI)
- [ ] ⭐⭐⭐ Service layer `batchProcessing.ts` (API integration)
- [ ] ⭐⭐⭐ Hook `useRunProgress` (polling state management)
- [ ] ⭐⭐ Client-side ZIP generation (using JSZip)
- [ ] ⭐⭐ Error handling & retry logic
- [ ] ⭐ Estimación de tiempo restante (basado en avg time/doc)

---

## Resumen Ejecutivo

### ¿Puede el frontend hacer procesamiento en lote sin scripts?

**✅ SÍ**, el backend actual ya tiene toda la funcionalidad necesaria:

1. **Upload**: `POST /projects/{project_id}/documents/upload` con múltiples archivos
2. **Create Run**: `POST /runs` con array de `document_ids`
3. **Monitor**: `GET /runs/{run_id}` para polling
4. **Download**: `GET /runs/{run_id}/exports` + `/artifacts/{run_id}/{filename}`

### Lo que falta (opcional, mejora UX):

1. **Backend**:
   - Endpoint para ZIP de correcciones (recomendado)
   - Endpoint de cancelación (nice to have)

2. **Frontend**:
   - Componentes UI para upload/progress/download
   - Lógica de polling y state management
   - Client-side ZIP si no quieres endpoint backend

### Tiempo estimado de implementación:

- **Solo Frontend** (usando backend actual): **2-3 días**
- **Frontend + mejoras backend** (ZIP endpoint): **3-4 días**
- **Full features** (cancelación, WebSockets): **5-7 días**

El MVP puede estar listo en **2-3 días** sin tocar el backend.
