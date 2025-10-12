# Checklist — Backend

Estado de alto nivel del backend (API, datos, colas, límites, despliegue). Mantener actualizado según AGENTS.md.

## Fundaciones y APIs
- [x] FastAPI app funcional (`server/main.py`) con routers modulares
- [x] Modelado y DB SQLite via SQLModel (`server/models.py`, `server/db.py`)
- [x] Auth: registro/login con JWT + bcrypt (`/auth/register`, `/auth/login`)
- [x] Proyectos: listar/crear/actualizar (`/projects`) con AutZ por owner
- [x] Documentos: subida/listado/descarga y almacenamiento en disco (`/projects/{id}/documents/...`)
- [x] Runs: crear y estado agregado (`/runs`) con validación de proyecto/usuario

## Almacenamiento y artefactos
- [x] Almacenamiento real en disco por usuario/proyecto (`server/storage.py`), checksum sha256
- [x] Configurar `STORAGE_DIR` (Docker: `/data`) y montar volumen en compose
- [x] Artefactos de exportación (JSONL/DOCX) registrados en DB (`exports`)
- [x] Endpoints para listar/descargar exportables de un run (`GET /runs/{id}/exports`, `GET /runs/{id}/exports/{export_id}/download`)
- [x] Endpoints directos: `GET /runs/{id}/changelog.csv`, `GET /runs/{id}/summary.md`

## Concurrencia, cuotas y planificación
- [x] Scheduler en memoria con fair‑share, cuotas por plan y `SYSTEM_MAX_WORKERS`
- [x] Encolar por documento respetando `max_docs_per_run` por plan
- [x] Cola persistente en DB (reconstrucción del scheduler en startup desde `RunDocument`)
- [x] Locks tipo lease por `RunDocument` con `locked_by/locked_at` y TTL (`LOCK_TTL_SECONDS`)
- [ ] Heartbeats y recuperación de tareas huérfanas
- [x] Worker de fondo: procesa `RunDocument` → integra motor y actualiza estados
- [ ] Cancelación y reintentos exponenciales con backoff

## Integración de pipeline
- [x] Integrar `corrector.engine` (HeuristicCorrector) para procesar DOCX/TXT desde `Document.path`
- [x] Generar y guardar exportables (JSONL/DOCX) por `RunDocument` (tabla `exports`)
- [x] CSV del log y carta editorial (`summary.md`) como exportables vinculados al `Run`
 
## Revisión interactiva y feedback (nuevo)
- [ ] Modelo de datos de revisión: `review_sessions` y `review_decisions` (token_id/suggestion_id, accepted|rejected|unset)
- [ ] `GET /runs/{id}/suggestions` (o exponer directo `*.corrections.jsonl` con metadata estable)
- [ ] `POST /runs/{id}/reviews` (guardar decisiones), `POST /runs/{id}/reviews/bulk`
- [ ] `GET /runs/{id}/preview` (aplicar decisiones sobre texto) y `POST /runs/{id}/finalize` (export final)
- [ ] `GET /runs/{id}/reviews/export` (dataset JSONL/CSV para entrenamiento)
- [ ] Agregador “apply decisions” estable por `token_id` y orden de aparición
- [ ] `suggestion_id` estable (hash doc_id|token_id|original|corrected|rule_id) y validación de idempotencia
- [ ] Filtros de bulk por `category`, `rule_id`, `doc_id`, `confidence_min`, `state=pending`
- [ ] Endpoint de previsualización “dry run” con streaming (HTML/TXT) y fallback DOCX temporal
- [ ] Auditoría/Historial de decisiones por sesión (quién, cuándo, lote)
- [ ] Export de dataset con anonimización y schema SFT/preferencias

## Detección/estilo y premium
- [ ] Detección de idioma/variante en ingesta/run (heurísticos) y guardado en `projects`/`runs`
- [ ] Perfil de estilo heurístico base y endpoint `/projects/{id}/style/auto-infer` (premium)
- [ ] Límite de presupuesto IA por plan y telemetría mínima

## Entrenamiento con feedback (modelos)
- [ ] Evaluar FT: Gemini 2.5 Flash (no FT directo) vs. OSS (Llama/Mistral) con LoRA/QLoRA
- [ ] Exportador de dataset SFT y preferencias (aceptadas vs rechazadas) anonimizado
- [ ] Pipeline offline para entrenamiento OSS y carga de pesos adaptativos (cuando aplique)

## Seguridad y privacidad
- [ ] JWT: refresh tokens, rotación y logout
- [ ] Rate limiting por plan y registro en `UsageLog`
- [ ] Validación de archivos: tamaños/extensiones/MIME; sanitización y revisión DOCX (macro)
- [ ] Invitados (sesiones efímeras), TTL y “claim” tras registro

## Observabilidad y migraciones
- [ ] Logging estructurado y correlación por run
- [ ] Métricas Prometheus (procesados, tiempos, colas)
- [ ] Alembic para migraciones

## Despliegue
- [x] Dockerfile multi‑stage y `docker-compose.yml` con volumen de `storage`
- [ ] Compose/plantillas para Postgres/Redis/MinIO (escalado)

## Documentación y tests
- [x] Plan actualizado: `docs/plan-backend.md` (paralelismo y almacenamiento)
- [x] Tests básicos: health, límites, auth, proyectos, subida y runs
- [ ] End‑to‑end: run real con motor y artefactos
