# Corrector Ortográfico/Contextual en Español

Corrector inteligente de documentos DOCX usando Google Gemini, especializado en detectar confusiones léxicas comunes del español (vello/bello, vaca/baca, hojear/ojear, etc.).

## 🎯 Características

- ✅ **Correcciones precisas a nivel de palabra** - No reescribe todo el texto, solo corrige errores específicos
- ✅ **Detección de confusiones léxicas** - Especializado en pares de palabras que suenan similar
- ✅ **Preservación de formato** - Mantiene estilos, negritas, cursivas, etc.
- ✅ **Logs detallados** - JSON + informe DOCX con tabla formateada
- ✅ **Procesamiento por chunks** - Maneja documentos largos de forma eficiente
- ✅ **Progreso visible** - Logs en tiempo real del procesamiento

## 📋 Requisitos

- Python 3.11.17 y uv 0.13.5
- API Key de Google Gemini ([obtener aquí](https://aistudio.google.com/app/apikey))

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone <repo-url>
cd corrector

# Instalar el proyecto local con el lock versionado
uv sync --frozen
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Configurar API key
cp .env.example .env
# Editar .env y añadir tu GOOGLE_API_KEY
```

## 💻 Uso

### Modo CLI

```bash
# Corregir un documento (salida en outputs/)
python -m corrector.cli documento.docx

# Especificar rutas de salida personalizadas
python -m corrector.cli documento.docx --out corregido.docx --log correcciones.jsonl
```

### Modo Servidor (REST API + Frontend)

```bash
# Desarrollo local con hot-reload (backend + frontend)
docker-compose -f docker-compose.dev.yml up

# Producción
docker-compose up -d
```

Una vez iniciado:
- **Frontend**: `http://localhost:5173` - Interfaz web para gestionar proyectos y correcciones
- **API**: `http://localhost:8001` - Documentación en `/docs`

#### Funcionalidades del Frontend

- ✅ **Autenticación**: Sistema de login/registro con JWT
- ✅ **Gestión de Proyectos**: Crear, listar y gestionar proyectos de corrección
- ✅ **Subida de Documentos**: Upload múltiple de archivos DOCX
- ✅ **Ejecución de Correcciones**: Crear runs y monitorear progreso en tiempo real
- ✅ **Tabla de Correcciones**: Visualización profesional con 3 modos de vista:
  - **Inline**: Contexto completo con original tachado → corregido resaltado
  - **Apilado**: Original y corregido en columnas separadas con frase completa
  - **Lado a lado**: Comparación visual del antes/después
- ✅ **Búsqueda y Filtrado**: Buscar correcciones por palabra, motivo o contexto
- ✅ **Descarga de Artefactos**: Acceso a documentos corregidos, logs JSONL y reportes DOCX

### Opciones avanzadas (CLI)

```bash
# Sin generar el reporte DOCX
python -m corrector.cli documento.docx --no-log-docx

# Usar corrector local sin API (solo para pruebas)
python -m corrector.cli documento.docx --local-heuristics

# Cambiar el modelo de Gemini
python -m corrector.cli documento.docx --model gemini-2.5-pro

# Desactivar preservación de formato
python -m corrector.cli documento.docx --no-preserve-format
```

## 📁 Estructura del Proyecto

```
corrector/
├── corrector/           # Motor de corrección
│   ├── cli.py          # CLI
│   ├── engine.py       # Procesamiento y chunking
│   ├── model.py        # Integración Gemini
│   ├── text_utils.py   # Tokenización
│   └── docx_utils.py   # I/O de DOCX
├── server/             # API REST
│   ├── main.py         # FastAPI app
│   ├── scheduler.py    # Scheduler fair-share
│   ├── limits.py       # Cuotas por plan
│   ├── models.py       # SQLModel schemas
│   ├── routes_*.py     # Endpoints organizados
│   └── worker.py       # Procesamiento en background
├── web/                # Frontend React
│   ├── src/
│   │   ├── components/ # CorrectionsTable, UI components
│   │   ├── pages/      # Projects, RunDetail, CorrectionsView
│   │   ├── contexts/   # AuthContext
│   │   ├── lib/        # api, auth, types
│   │   └── layouts/    # Layout principal
│   ├── Dockerfile      # Imagen frontend
│   └── vite.config.ts  # Configuración Vite
├── tests/
│   ├── samples/        # Documentos de test
│   ├── outputs/        # Salidas de test (gitignored)
│   └── test_*.py       # Tests unitarios e integración
├── docs/               # Documentación
│   ├── base-prompt.md  # Prompt de Gemini
│   ├── frontend-plan.md # Plan y progreso del frontend
│   └── ui-plan.md      # Plan detallado de UI
├── outputs/            # Salidas de producción (gitignored)
├── Dockerfile          # Imagen Docker multi-stage
├── docker-compose.yml  # Despliegue producción
└── docker-compose.dev.yml  # Desarrollo con hot-reload
```

**Nota**: Los documentos `.docx` de usuario no se trackean en git. Solo se incluyen documentos de ejemplo específicos en `examples/ejemplo_*.docx` y muestras de test en `tests/samples/`.

## 📊 Archivos Generados

Por defecto, los archivos se guardan en `outputs/`:

- `documento.corrected.docx` - Documento corregido
- `documento.corrections.jsonl` - Log detallado en JSON (una corrección por línea)
- `documento.corrections.docx` - Informe con tabla formateada
 - `documento.changelog.csv` - CSV persistente del log
 - `documento.summary.md` - Carta de edición con métricas y motivos

### Formato del log JSONL

```json
{
  "token_id": 3481,
  "line": 39,
  "original": "rio",
  "corrected": "rió",
  "reason": "El pretérito perfecto simple del verbo 'reír' lleva tilde",
  "context": "Daniel rio con",
  "chunk_index": 1,
  "sentence": "Daniel rio con ganas."
}
```

## 🎨 Informe DOCX

El informe generado incluye una tabla profesional con:
- **Encabezados con fondo azul**
- **Original en rojo → Corregido en verde**
- **Columnas**: #, Original → Corregido, Motivo, Contexto, Línea

## ⚙️ Configuración

### Variables de Entorno (.env)

```bash
# API Key de Google Gemini
GOOGLE_API_KEY=tu_api_key_aqui

# Modelo a usar (por defecto: gemini-2.5-flash)
GEMINI_MODEL=gemini-2.5-flash

# Para tests de integración
RUN_GEMINI_INTEGRATION=0
```

### Personalizar el Prompt

Edita `docs/base-prompt.md` para ajustar las instrucciones de corrección.

## 🐋 Docker

### Configuración

Crea archivo `.env`:
```bash
GOOGLE_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-2.5-flash
DEMO_PLAN=free
SYSTEM_MAX_WORKERS=2
```

### Comandos Docker

```bash
# Construir imagen
docker-compose build

# Ejecutar en background
docker-compose up -d

# Ver logs
docker-compose logs -f corrector-api

# Detener
docker-compose down
```

### Desarrollo con Docker

```bash
# Hot-reload automático
docker-compose -f docker-compose.dev.yml up
```

Los cambios en código se reflejan automáticamente sin reconstruir imagen.

## 📦 Procesamiento por Lotes (Batch Processing)

El servidor API soporta procesamiento de múltiples documentos en un solo run, con rate limiting inteligente y retry automático.

### Características del Batch Processing

- ✅ **Rate Limiting automático**: Respeta límites de API según modelo
  - `gemini-2.5-pro`: 2 req/min (30s entre requests)
  - `gemini-2.5-flash`: 15 req/min (4s entre requests)
- ✅ **Retry con backoff exponencial**: 3 reintentos con delays de 2s, 4s, 8s
- ✅ **Fallback inteligente**: Si pro falla, usa flash solo para ese chunk
- ✅ **Monitoreo en tiempo real**: API de status con progreso
- ✅ **Descarga de resultados**: Extrae solo archivos `.corrections.docx`

### Ejemplo de Uso

```python
import requests
from pathlib import Path
import time

API_URL = "http://localhost:8001"
EMAIL = "demo@example.com"
PASSWORD = "demo123"

# 1. Autenticar
resp = requests.post(f"{API_URL}/auth/login",
                     json={"email": EMAIL, "password": PASSWORD})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Obtener proyecto
resp = requests.get(f"{API_URL}/projects", headers=headers)
project_id = resp.json()[0]["id"]

# 3. Subir documentos (batch)
docx_files = sorted(Path("documentos").glob("*.docx"))
files_to_upload = [
    ("files", (f.name, open(f, "rb"),
     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    for f in docx_files
]
resp = requests.post(
    f"{API_URL}/projects/{project_id}/documents/upload",
    headers=headers,
    files=files_to_upload
)
for _, (_, f, _) in files_to_upload:
    f.close()

document_ids = [doc["id"] for doc in resp.json()]
print(f"✅ Subidos {len(document_ids)} documentos")

# 4. Crear run con todos los documentos
resp = requests.post(
    f"{API_URL}/runs",
    headers=headers,
    json={"project_id": project_id, "document_ids": document_ids, "use_ai": True}
)
run_id = resp.json()["run_id"]
print(f"📋 Run creado: {run_id}")

# 5. Monitorear progreso
while True:
    resp = requests.get(f"{API_URL}/runs/{run_id}", headers=headers)
    status_data = resp.json()
    status = status_data["status"]
    processed = status_data.get("processed_documents", 0)
    total = status_data.get("total_documents", 0)

    print(f"[{processed}/{total}] Status: {status}")

    if status in ["completed", "failed"]:
        break

    time.sleep(10)

# 6. Descargar correcciones
resp = requests.get(f"{API_URL}/runs/{run_id}/exports", headers=headers)
exports = resp.json()

corrections_files = [e for e in exports if e["category"] == "log_docx"]
output_dir = Path("correcciones_finales")
output_dir.mkdir(exist_ok=True)

for export in corrections_files:
    filename = export["name"]
    resp = requests.get(f"{API_URL}/artifacts/{run_id}/{filename}", headers=headers)

    with open(output_dir / filename, "wb") as f:
        f.write(resp.content)

    print(f"📥 Descargado: {filename}")

print(f"✅ Completado! {len(corrections_files)} archivos en {output_dir}")
```

### Tiempos Estimados

Con rate limiting activo:
- **gemini-2.5-pro**: ~30s por documento (120 docs/hora)
- **gemini-2.5-flash**: ~4s por documento (900 docs/hora)

Para 41 documentos con pro: ~20 minutos

## 🧪 Tests

```bash
# Tests unitarios (sin API)
pytest tests/test_text_utils.py tests/test_engine_apply.py

## 📌 Progreso

- Checklists vivos del proyecto (se actualizan con cada cambio):
  - Backend: `progress/backend-checklist.md`
  - Core: `progress/core-checklist.md`
  - Frontend: `progress/frontend-checklist.md`

### Última actualización (S3)
- ✅ **UI de revisión interactiva con aceptación/rechazo en tabla**: Sistema completo de gestión de sugerencias integrado en `CorrectionsView` con:
  - Detección automática de modo servidor (API persistente) vs legacy (JSONL)
  - Botones inline para aceptar/rechazar correcciones individuales
  - Selección múltiple con checkboxes y acciones masivas
  - Barra de progreso visual con segmentos de estado (pendientes/aceptadas/rechazadas)
  - Filtros por status con tabs dinámicos
  - Exportación DOCX con solo correcciones aceptadas
  - Retrocompatibilidad completa con runs antiguos


# Tests con mock de Gemini
pytest tests/test_gemini_fake.py

# Tests del servidor
pytest tests/test_server_basic.py

# Tests de integración (requiere API key y RUN_GEMINI_INTEGRATION=1)
pytest tests/test_gemini_live.py
```

## 🔧 Notas Técnicas

### Chunking Inteligente

- **Auto-chunking**: Divide documentos largos en chunks de ~300-1000 palabras (15% de la ventana de contexto)
- **Overlap**: 10% de solapamiento entre chunks para mantener coherencia
- **Límites naturales**: Respeta fin de oración y párrafos

### Filtrado de Falsos Positivos

El motor filtra automáticamente:
- Correcciones donde original == reemplazo
- Correcciones de espacios/puntuación a palabras (token IDs incorrectos)
- Palabras ya correctas pero marcadas como "explicación"

### Preservación de Formato

- Mantiene todos los estilos originales (negritas, cursivas, colores, etc.)
- Solo reescribe el texto de los nodos `w:t` en el XML
- Preserva runs, párrafos y estructura del documento

## 📝 Ejemplos de Correcciones

El corrector detecta errores como:

- ✅ `rio` → `rió` (falta de tilde verbal)
- ✅ `contemplado` → `contemplando` (participio vs gerundio)
- ✅ `vello` → `bello` (confusión léxica por contexto)
- ✅ `baca` → `vaca` (si el contexto es animal, no portaequipajes)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto.

## Dependency maintenance - 2026-10-22

Node 24.22.1; Python 3.11.17 / uv 0.13.5. Frozen install commands, compatible dependency cohorts, offline checks and remaining verification limits are recorded in [SECURITY-DEPENDENCIES.md](SECURITY-DEPENDENCIES.md).
