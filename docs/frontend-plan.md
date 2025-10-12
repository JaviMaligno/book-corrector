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

## Roadmap (4–6 semanas)
- S1: Scaffold SPA, paleta y visor JSONL.
- S2: Proyectos, upload, runs y artefactos (polling).
- S3: CorrectionsTable conectada a API, filtros/segmentación.
- S3.5: UI de Revisión (A/R individual, panel lateral, bulk y “aceptar por defecto”).
- S4: Persistencia backend de decisiones, preview/finalize y export de dataset.
- S5: Glosario/estilo básico, modo Rápido/Profesional, pulido UX.
- Extra: SSE/WebSocket, visor DOCX, autenticación guest/usuario.
- Extra: SSE/WebSocket, visor DOCX, autenticación guest/usuario.
