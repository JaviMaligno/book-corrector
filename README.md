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

### Uso básico

```bash
# Corregir un documento (salida en outputs/)
python -m corrector.cli documento.docx

# Especificar rutas de salida personalizadas
python -m corrector.cli documento.docx --out corregido.docx --log correcciones.jsonl
```

### Opciones avanzadas

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
├── corrector/           # Código fuente
│   ├── cli.py          # Interfaz de línea de comandos
│   ├── engine.py       # Motor de procesamiento
│   ├── model.py        # Integración con Gemini
│   ├── prompt.py       # Gestión de prompts
│   ├── text_utils.py   # Tokenización y utilidades
│   ├── docx_utils.py   # Lectura/escritura de DOCX
│   └── llm.py          # Cliente de Gemini
├── tests/              # Tests
│   ├── samples/        # Documentos para tests
│   └── test_*.py       # Tests unitarios e integración
├── outputs/            # Archivos generados (gitignored)
├── examples/           # Documentos de ejemplo (solo ejemplo_*.docx)
├── base-prompt.md      # Prompt base para Gemini
├── settings.py         # Configuración
├── .env               # Variables de entorno (gitignored)
├── .env.example       # Plantilla de configuración
└── .gitignore         # Excluye todos los .docx excepto tests/samples y ejemplos
```

**Nota**: Los documentos `.docx` de usuario no se trackean en git. Solo se incluyen documentos de ejemplo específicos en `examples/ejemplo_*.docx` y muestras de test en `tests/samples/`.

## 📊 Archivos Generados

Por defecto, los archivos se guardan en `outputs/`:

- `documento.corrected.docx` - Documento corregido
- `documento.corrections.jsonl` - Log detallado en JSON (una corrección por línea)
- `documento.corrections.docx` - Informe con tabla formateada

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

Edita `base-prompt.md` para ajustar las instrucciones de corrección.

## 🧪 Tests

```bash
# Tests unitarios (sin API)
pytest tests/test_text_utils.py tests/test_engine_apply.py

# Tests con mock de Gemini
pytest tests/test_gemini_fake.py

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
