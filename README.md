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

- Python 3.10+
- API Key de Google Gemini ([obtener aquí](https://aistudio.google.com/app/apikey))

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone <repo-url>
cd corrector

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -e .

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

### Modo Servidor (REST API)

```bash
# Desarrollo local
uvicorn server.main:app --reload

# Docker (producción)
docker-compose up -d

# Docker (desarrollo con hot-reload)
docker-compose -f docker-compose.dev.yml up
```

Ver documentación de API en `http://localhost:8000/docs`

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
│   └── schemas.py      # Modelos Pydantic
├── tests/
│   ├── samples/        # Documentos de test
│   ├── outputs/        # Salidas de test (gitignored)
│   └── test_*.py       # Tests unitarios e integración
├── docs/               # Documentación
│   └── base-prompt.md  # Prompt de Gemini
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

## 🧪 Tests

```bash
# Tests unitarios (sin API)
pytest tests/test_text_utils.py tests/test_engine_apply.py

## 📌 Progreso

- Checklists vivos del proyecto (se actualizan con cada cambio):
  - Backend: progress/backend-checklist.md
  - Core: progress/core-checklist.md


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
