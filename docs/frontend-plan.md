# Plan de Frontend (MVP)

Este plan concreta una SPA ligera para operar “por proyecto”, alineada con docs/market-analysis.md y los planes de backend/core.

## Objetivos UX
- Subir, configurar y corregir en 3–4 pasos con feedback claro.
- Dos modos: Rápido (sencillo) y Profesional (filtros, glosario, paquetes de reglas).
- Descargas visibles (DOCX/JSONL) y visor de correcciones usable sin backend.

## Arquitectura
- Stack: Vite + React + TypeScript + Tailwind, TanStack Query.
- Rutas: `/` (Visor JSONL), `/projects`, `/projects/:id`, `/runs/:runId`.
- API: FastAPI (MVP) con endpoints: health, projects (CRUD mínimo), upload, runs, artifacts.

## Páginas y Componentes
- Visor JSONL: carga local; vistas Inline, Antes/Después y Lado a lado; búsqueda por palabra/razón/contexto.
  - También soporta carga remota vía `?jsonlUrl=` apuntando a `/artifacts/{runId}/{file}.jsonl` de la API.
- Proyectos: creación (nombre, variante, modo) y lista.
- Detalle de Proyecto: subida múltiple, lista de documentos, “Corregir”.
- Detalle de Run: estado con polling y enlaces a artefactos.
- Componentes clave: Dropzone (futuro), Stepper, CorrectionsTable, ContextSnippet.

### Revisión interactiva (nuevo)
- Ver plan unificado en `docs/ui-plan.md` (tri‑panel, acciones granulares y por lotes, previsualización, datasets de feedback y detalles de endpoints). Este archivo mantiene solo el resumen y el encaje con el resto del frontend.

## Diseño y Marca
- Paleta: Azul tinta `#16355B`, Verde revisión `#20C997`, Rojo corrección `#E63946`, fondo papel `#FAF7F2`.
- Tipografías: Inter (UI) y Source Serif 4 (contenido, fase siguiente).
- Semántica: original tachado rojo, flecha gris, corregido verde con énfasis.

## Integración Backend
- Dev: polling 2–3 s; SSE/WebSocket en fase 2.
- Artefactos: `GET /runs/{id}/artifacts` y `GET /artifacts/{id}/{file}`.
- Producción: `docker-compose.yml` con web (Nginx) + api (Uvicorn).

### Endpoints, modelo y dataset
- Detalles completos en `docs/ui-plan.md` (endpoints de `suggestions`, `reviews`, `bulk`, `preview`, `finalize` y `reviews/export`; modelo `review_sessions/review_decisions`; dataset SFT/preferencias y privacidad).

## Roadmap y Progreso

### ✅ Completado (S1-S2)
- [x] Scaffold SPA con Vite + React + TypeScript + Tailwind
- [x] Paleta de colores y diseño básico
- [x] Sistema de autenticación (login/register con JWT)
- [x] Gestión de proyectos (crear, listar, detalle)
- [x] Subida de documentos (upload múltiple)
- [x] Runs y monitoreo con polling
- [x] Listado de artefactos
- [x] **CorrectionsView**: Página de visualización de correcciones
- [x] **CorrectionsTable**: Componente con 3 modos de vista:
  - Inline (contexto completo con original tachado → corregido)
  - Apilado (columnas separadas con frase completa)
  - Lado a lado (comparación antes/después)
- [x] Búsqueda en tiempo real (palabra, motivo, contexto)
- [x] Integración con API autenticada (axios interceptors)
- [x] Descarga de artefactos (DOCX corregidos, logs JSONL, reportes)

### ✅ Completado (S3)
- [x] **UI de Revisión interactiva integrada en CorrectionsView**:
  - [x] Detección automática modo servidor (API) vs legacy (JSONL)
  - [x] Aceptar/Rechazar individual con botones inline en cada fila
  - [x] Checkboxes de selección múltiple
  - [x] Operaciones en bulk: "Aceptar seleccionadas (N)" y "Rechazar seleccionadas (N)"
  - [x] "Aceptar todas pendientes" y "Rechazar todas pendientes" con confirmaciones
  - [x] Barra de progreso visual (verde/amarillo/rojo) con % completado
  - [x] Filtros por status (Todas, Pendientes, Aceptadas, Rechazadas)
  - [x] Badges de estado y tipo de corrección en cada fila
  - [x] Exportación DOCX con solo correcciones aceptadas
  - [x] Mutaciones con TanStack Query e invalidación automática
  - [x] Retrocompatibilidad con runs legacy (JSONL)
- [x] **API Integration** (`web/src/lib/suggestions.ts`):
  - [x] `listSuggestions(runId, status?)` - GET con filtro opcional
  - [x] `updateSuggestionStatus(id, status)` - PATCH individual
  - [x] `bulkUpdateSuggestions(runId, ids, status)` - POST bulk
  - [x] `acceptAllSuggestions(runId)` - POST accept-all
  - [x] `rejectAllSuggestions(runId)` - POST reject-all
  - [x] `exportWithAccepted(runId)` - POST export DOCX
- [x] Estadísticas y métricas del run (contadores pendientes/aceptadas/rechazadas)

### 🚧 En Progreso (S3.5)
- [ ] Filtros avanzados por tipo de error, severidad y confianza
- [ ] Segmentación y navegación por categorías de corrección
- [ ] Virtualización de listas para >10k sugerencias

### 📋 Pendiente (S4-S5)
- [ ] UI de Revisión avanzada:
  - [ ] Panel lateral con contexto expandido y metadata adicional
  - [ ] Vista de comparación antes/después con scroll sincronizado
  - [ ] Atajos de teclado (A/R/U, ↑/↓)
- [ ] Backend de decisiones extendido:
  - [ ] Persistencia de review_sessions (opcional, actualmente inline)
  - [ ] Preview del documento final (dry-run)
  - [ ] Export de dataset de feedback (SFT/preferencias)
- [ ] Modo Rápido vs Profesional:
  - [ ] Glosario personalizado
  - [ ] Paquetes de reglas
  - [ ] Configuración de estilo
- [ ] Pulido UX:
  - [ ] Mejoras de accesibilidad
  - [ ] Atajos de teclado
  - [ ] Onboarding/tour

### 🎁 Extras Futuros
- [ ] SSE/WebSocket para updates en tiempo real
- [ ] Visor DOCX integrado
- [ ] Autenticación guest/usuario (actualmente solo usuario registrado)
- [ ] Export a otros formatos (PDF, Markdown)

## Checklist Detallado por Componente

### Autenticación (`web/src/contexts/AuthContext.tsx`, `web/src/lib/auth.ts`)
- [x] AuthContext con login/register/logout
- [x] Almacenamiento de tokens en localStorage
- [x] Interceptor axios para añadir Authorization header automáticamente
- [x] getCurrentUser para verificar sesión
- [x] Manejo de errores 401/403
- [ ] Refresh token automático
- [ ] Remember me / persistent session

### Páginas Core
#### Projects (`web/src/pages/Projects.tsx`)
- [x] Lista de proyectos con polling
- [x] Crear nuevo proyecto (nombre, variante, modo)
- [x] Navegación a detalle de proyecto
- [x] Protección de ruta (solo autenticados)
- [ ] Editar proyecto existente
- [ ] Eliminar proyecto
- [ ] Búsqueda/filtrado de proyectos

#### ProjectDetail (`web/src/pages/ProjectDetail.tsx`)
- [x] Vista de detalle del proyecto
- [x] Subida múltiple de documentos DOCX
- [x] Lista de documentos del proyecto
- [x] Crear run con documentos seleccionados
- [x] Lista de runs del proyecto
- [x] Navegación a detalle de run
- [ ] Eliminar documentos
- [ ] Renombrar documentos
- [ ] Preview de documentos

#### RunDetail (`web/src/pages/RunDetail.tsx`)
- [x] Estado del run (queued/processing/completed)
- [x] Polling automático cada 2s
- [x] Progreso (procesados/total)
- [x] Lista de artefactos generados
- [x] Card destacado si hay correcciones disponibles
- [x] Botón para ver tabla de correcciones
- [x] Links de descarga de artefactos
- [ ] Cancelar run en progreso
- [ ] Log de errores si run falla
- [ ] Métricas del run (tiempo, tokens, costo)

#### CorrectionsView (`web/src/pages/CorrectionsView.tsx`)
- [x] Carga de archivo .corrections.jsonl desde artifacts
- [x] Parsing de JSONL a array de correcciones
- [x] Integración con CorrectionsTable
- [x] Manejo de estados de carga/error
- [x] Título con ID del run
- [x] Autenticación correcta (usa api axios con interceptor)
- [ ] Paginación si hay muchas correcciones
- [ ] Descarga del JSONL filtrado
- [ ] Compartir vista de correcciones (URL pública)

### Componentes de UI
#### CorrectionsTable (`web/src/components/CorrectionsTable.tsx`)
- [x] Modo Inline (contexto completo con resaltado)
- [x] Modo Apilado (columnas original/corregido)
- [x] Modo Lado a lado (comparación visual)
- [x] Selector de modo de vista
- [x] Búsqueda en tiempo real (palabra, motivo, contexto)
- [x] Resaltado del término buscado
- [x] Contador de resultados
- [x] Manejo de casos edge (sin sentence, sin context)
- [x] Diseño responsive
- [ ] Ordenar por columna (línea, original, chunk_index)
- [ ] Filtros por tipo de error
- [ ] Export a CSV/Excel
- [ ] Acciones de revisión (aceptar/rechazar)
- [ ] Navegación con teclado

#### Layout (`web/src/layouts/Layout.tsx`)
- [x] Navegación principal con tabs
- [x] Menú de usuario (logout)
- [x] Logo y branding
- [x] Outlet para rutas hijas
- [ ] Breadcrumbs
- [ ] Notificaciones toast
- [ ] Indicador de estado de conexión

### API Integration (`web/src/lib/api.ts`)
- [x] Cliente axios base con baseURL
- [x] Timeout de 20s
- [x] Función ping para health check
- [x] Integración con auth interceptor
- [ ] Retry automático en errores de red
- [ ] Interceptor de respuestas para errores globales
- [ ] Request cancellation
- [ ] Progress tracking para uploads

### Tipos y Modelos (`web/src/lib/types.ts`)
- [x] CorrectionRow (token_id, original, corrected, reason, context, sentence, line, chunk_index)
- [ ] Project, Document, Run types completos
- [ ] Export types
- [ ] User, AuthTokens (actualmente en auth.ts)
- [ ] API response types

## Estado Actual: S2 Completado ✅

El MVP básico está funcional con:
- Autenticación completa
- CRUD de proyectos
- Upload de documentos
- Ejecución y monitoreo de runs
- **Visualización profesional de correcciones con 3 modos de vista**
- Búsqueda y descarga de artefactos

**Siguiente paso**: S3 - Filtros avanzados y estadísticas
