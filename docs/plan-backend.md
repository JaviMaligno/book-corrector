# Plan de Backend — Lógica, Datos y Escalabilidad

Este documento detalla la arquitectura backend que soporta el core functionality y los nuevos requisitos: acceso persistente para usuarios registrados, sesiones efímeras para invitados, límites free vs premium, detección de idioma y auto‑inferencia (premium) de estilo/época/región/personajes. Optimizado para coste cero inicial y con vías claras de escalado.

## Objetivos
- Persistencia y seguridad: proyectos/correcciones de usuarios registrados, invitados efímeros.
- Diferenciadores: trazabilidad total, DOCX con track changes, consistencia intercapítulos, perfiles de estilo/personajes.
- Control de costes: stack OSS, single‑node; migrable a componentes escalables.

## Arquitectura (MVP costo cero)
- API: FastAPI (Python) + Uvicorn.
- Auth: JWT con refresh tokens; `passlib` para hashes; invitado con sesión firmada (cookie).
- DB: SQLite + SQLAlchemy/SQLModel; migraciones con Alembic.
- Almacenamiento: sistema de ficheros (`storage/`) para subidas y artefactos; rutas por usuario/proyecto.
- Jobs: tareas asíncronas con `asyncio`/BackgroundTasks (sin broker). Para runs largos, proceso worker separado invocado por CLI.
- Rate limiting/quotas: `slowapi` (memoria) o middleware propio con contador en DB.
- Observabilidad: logging estructurado (JSON), métricas básicas (Prometheus opcional cuando se escale).

Escalado futuro
- DB → Postgres. Sesiones/colas/cache → Redis. Objetos → MinIO/S3. Jobs → Celery/RQ/Dramatiq. Búsqueda → OpenSearch. 
- Tiempo real → WebSocket + Redis Pub/Sub. Multi‑instancia detrás de Nginx/Traefik.

## Almacenamiento de Archivos (Subida Real)
- Directorio base configurable: `STORAGE_DIR` (por defecto `./storage`, en Docker `/data`).
- Esquema: `STORAGE_DIR/{user_id}/{project_id}/{checksum8}_{nombre}`.
- Cálculo de checksum sha256 en streaming y guardado atómico (archivo temporal → destino).
- Modelado: `documents.path`, `documents.checksum`, `documents.kind`, `status=ready` tras subida.
- Endpoints:
  - `POST /projects/{id}/documents/upload` (multipart, múltiple) → crea `Document` por archivo.
  - `GET /projects/{id}/documents` → lista documentos.
  - `GET /projects/{id}/documents/{doc_id}/download` → descarga.
  - Unicidad de nombre por proyecto: si choca, se sufija ` (n)` automáticamente.

## Exportables (Listado y Descarga)
- Tabla `exports` enlaza `run_id` con ficheros generados (corrected.docx, corrections.jsonl, corrections.docx).
- Endpoints:
  - `GET /runs/{run_id}/exports` → lista exportables con `id`, `kind`, `name`, `category`, `size`.
  - `GET /runs/{run_id}/exports/{export_id}/download` → descarga un exportable.
  - `GET /runs/{run_id}/exports/csv` → (opcional) CSV del changelog agregado (complementario al CSV persistente).
  - `GET /runs/{run_id}/changelog.csv` → descarga el CSV persistente si existe (fallback al agregado).
  - `GET /runs/{run_id}/summary.md` → descarga la carta editorial persistente.

Persistencia de exportables
- El worker genera persistentemente:
  - `*.corrected.docx|txt`: documento corregido.
  - `*.corrections.jsonl`: log detallado.
  - `*.corrections.docx`: informe de correcciones.
  - `*.changelog.csv`: CSV del log (persistente).
  - `*.summary.md`: carta de edición (persistente) con conteos y motivos principales.

## Paralelismo, Concurrencia y Planificación

Granularidad segura (por defecto)
- Paralelismo por documento (capítulo) dentro de un mismo run de proyecto. No se paralelizan páginas arbitrarias.
- Segmentación intra‑documento determinista a nivel de tokens y párrafos (evitar “páginas” por su inestabilidad en DOCX/flujo).

Intra‑documento (opt‑in, cuidadoso)
- Para documentos muy largos, se permite paralelizar por bloques no solapados de párrafos/sentencias. Reglas:
  - Definir ventanas por “rangos de tokens” usando `corrector.text_utils.tokenize` para offsets estables.
  - No usar solapamiento en modo paralelo; si se requiere ventana con solape, se deduplica por `token_id` y `hash(before→after, reason)`.
  - Un “paso de consolidación” posterior resuelve conflictos e impone orden estable por `token_id`.

Gestión de límites simultáneos (planes)
- Por usuario: `max_runs_concurrent` y `max_docs_concurrent` activos.
- Por run: `max_docs_per_run` (p. ej., Free=1, Premium=3).
- Global: `system_max_workers` para no saturar CPU/IO.

Planificador (scheduler)
- Cola por usuario con fair‑share (round‑robin ponderado por plan). Selecciona el siguiente documento runnable sin superar límites.
- Estados: `queued` → `processing` → `exporting` → `completed|failed|canceled`.
- Backpressure: cuando alcanza límites, permanece en `queued`; se reintenta al liberar slots.
- Persistencia: al iniciar, se reconstruye la cola desde DB (`RunDocument.status=queued`).

Bloqueos y consistencia
- Lease en DB: `RunDocument.locked_by/locked_at` con TTL (`LOCK_TTL_SECONDS`); el worker toma la tarea si el lease está libre o expirado.
- Prohibido ejecutar dos runs que modifiquen el mismo documento simultáneamente; si se lanza un segundo, queda `queued` con motivo.
- Heartbeats (a añadir): actualización periódica `heartbeat_at` para recuperación de tareas huérfanas.
- En SQLite: transacciones `BEGIN IMMEDIATE` para secciones críticas y columna `version` para control optimista.

Export y alineación
- La segmentación usa offsets de token global para que `track changes` y `changelog` se alineen incluso con trabajo paralelo.
- No se introducen reflujo de párrafos en pasos intermedios; la reescritura se aplica tras consolidación global.

Configurables por defecto (MVP)
- Free: `max_runs_concurrent=1`, `max_docs_per_run=1`, `max_docs_concurrent=1`.
- Premium: `max_runs_concurrent=2`, `max_docs_per_run=3`, `max_docs_concurrent=3`.
- Global: `system_max_workers=2` (MVP mononodo), `chunk_parallelism=false` por defecto.

## Modelo de Datos (tablas principales)
- `users` (id, email, hash, role: free|premium|admin, created_at, deleted_at)
- `sessions` (id, user_id|null, kind: guest|user, expiry, meta)
- `subscriptions` (user_id, plan, period, status, limits_json)
- `projects` (id, owner_id, name, lang_variant, style_profile_id, config_json, created_at)
- `documents` (id, project_id, path, kind: docx|txt|md, checksum, status)
- `runs` (id, project_id, submitted_by, mode: rapido|profesional, status, params_json, started_at, finished_at)
- `suggestions` (id, run_id, document_id, location, type, severity, before, after, reason, citation_id, source: rule|llm, confidence)
- `exports` (id, run_id, kind: docx|csv|jsonl|md, path)
- `style_profiles` (id, project_id, derived_from_run_id|null, data_json, era, region, treatment, quotes_style, numeric_style, leismo, solo_tilde, persona_rules)
- `characters` (id, project_id, name, traits_json)
- `glossary_terms` (id, project_id, term, preferred, notes)
- `normative_catalog` (id, source, ref, title, snippet)
- `usage_log` (id, user_id, metric, amount, at)

Notas
- JSONs están acotados a configuración/caches; lo auditable (sugerencias, citas) va normalizado.
- Invitados almacenan `projects/runs` con `owner_id = null` y `expiry` en 24–72h; al registrarse, se reclaman por `session_id`.

## Límites y Planes (free vs premium)
- Free: proyectos activos ≤2, tamaño por run ≤40k palabras, 1 run concurrente, retención 7–14 días, sin auto‑inferencia IA, export DOCX habilitada con marca “generated by”.
- Premium: proyectos ilimitados razonables, tamaño por run ≤200k palabras, 3–5 concurrentes, retención configurable, auto‑inferencia IA de estilo/época/región/personajes, reglas personalizadas y diccionarios por equipo, prioridad de cola.
- Rate limit API (ejemplo): 60 req/min free; 300 req/min premium. Presupuestos IA por proyecto/mes.

## Gestión de Sesiones y Acceso
- Invitados: cookie `sid` firmada; datos en `sessions` y artefactos bajo `storage/guests/{sid}/` con TTL.
- Registro/login: email+password (MVP). JWT access (15 min) + refresh (30 días). Opcional SSO a futuro.
- Propiedad y permisos: todo recurso ligado a `owner_id` o `session_id`. Endpoints validan aislamiento.

## Pipeline de Procesamiento (Runs)
1) Ingesta: subir DOCX/TXT/MD → `documents` con checksum.
2) Detección de idioma/variante (heurísticos + modelo ligero) y normalización Unicode.
3) Construcción de contexto: `project.yaml` + `style_profile` + `glossary` + `normative_catalog`.
4) Reglas deterministas (ortografía, puntuación, concordancia, consistencia); producir `suggestions` con citas.
5) IA (opcional/premium): reescrituras limitadas y auto‑perfiles; budget checks y chunking.
6) Agregación y scoring de confianza; consolidación de conflictos.
7) Exportables: CSV/JSONL de logs; DOCX con track changes; carta editorial (`summary.md`).
8) Persistir `runs` + `exports`; actualizar `projects`/`style_profiles`.

## Auto‑Inferencia (Premium) — Diseño de Chunking y Señales
- Muestreo estratificado del manuscrito: inicio/medio/final, páginas con diálogo alto, páginas de narración expositiva, secciones con números/fechas.
- Longitud por chunk: 800–1200 tokens; máximo N chunks por run según plan/retención.
- Señales a estimar por heurísticos y confirmar con IA: 
  - Tratamiento (tú/usted, voseo), comillas («»/“ ”/' '), punto y coma/coma serial, formato numérico (1.234,56 vs 1,234.56), tildado de «solo», leísmo/laísmo.
  - Registro/época (n‑gramas y léxico: “vuesa merced”, “ansí”, etc.).
  - Rasgos de personajes: muletillas, formalidad, longitud media de intervención, puntuación idiosincrática.
- Prompting: pedir resúmenes normativos estructurados (JSON) con confiabilidad y ejemplos textuales citados (offsets) para auditoría.
- Privacidad: desactivar entrenamiento con datos; limitar cotexto a lo mínimo necesario; ofuscar nombres propios en prompts si procede.

Fallback sin coste
- Si no hay IA disponible, generar `style_profile` con heurísticos + reglas; marcar como `inferred=false|weak` para UX.

## API (endpoints principales)
- `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`
- `GET/POST /projects`, `GET/PATCH /projects/{id}` (config: idioma, variante, estilo, época, región)
- `POST /projects/{id}/documents` (subida), `GET /projects/{id}/documents`
- `POST /projects/{id}/runs` (params: modo, paquetes de reglas, uso IA), `GET /runs/{id}` (status), `GET /runs/{id}/suggestions`, `GET /runs/{id}/exports/{kind}`
- `POST /projects/{id}/style/auto-infer` (premium), `GET/PATCH /projects/{id}/style`
- `GET /me/limits` (cuotas y consumo), `GET /me/exports`, `GET /health`

Estados de run
- `queued` → `processing` → `exporting` → `completed` | `failed` | `canceled`.

## Seguridad y Privacidad
- Hash de contraseñas `argon2` o `bcrypt`; JWT con rotación de refresh.
- AutZ por recurso; validación estricta de owner/session.
- Escaneo/limpieza de DOCX (zip) para evitar macros; límite de tamaño.
- Logs sin datos sensibles; opción de purga por proyecto.

## Retención y Migración
- Invitados: TTL 7–14 días; limpieza programada.
- Usuarios: retención por plan; borrado “hard delete” a petición.
- Migración al escalar: scripts para pasar SQLite→Postgres, FS→S3/MinIO, BackgroundTasks→Celery/Redis.

## Métricas y Cuotas (implementación)
- Contadores por usuario/mes: palabras procesadas, runs, tokens IA consumidos, exportaciones.
- Límite duro por plan; soft warnings al 80/90%.

## Plan de Entrega Backend (6–8 semanas)
- Sem 1: Esqueleto FastAPI, auth, modelos base, proyectos/documentos, subida de ficheros.
- Sem 2: Runs secuenciales con el motor de reglas existente, logs CSV/JSONL, límites básicos.
- Sem 3: Export DOCX con track changes, carta editorial; invitado efímero + “claim” tras registro.
- Sem 4: Inspector de consistencia intercapítulos; style_profile manual.
- Sem 5: Detección idioma/variante; perfiles de estilo con heurísticos; métricas/cuotas por plan.
- Sem 6: Auto‑inferencia IA (premium) con chunking y presupuesto; consolidación de estilo/personajes.
- Sem 7–8: Endurecimiento, pruebas de carga, migraciones Postgres/Redis opcionales y empaquetado Docker.

## Coste cero hoy, escalable mañana
- Hoy: 1 servidor/VM con FastAPI + SQLite + disco; sin colas externas; polling en lugar de websockets.
- Mañana: Postgres, Redis, MinIO/S3, Celery; autoscaling de workers. Mantener compatibilidad a nivel de API y migraciones.

## Buenas Prácticas y Dockerización
- Estilo y lint: Black + Ruff (config en `pyproject.toml`).
- Makefile: `fmt`, `lint`, `test`, `run`, `docker-build`, `docker-run`.
- Testing: pruebas básicas del servidor (`tests/test_server_basic.py`), TestClient de FastAPI.
- Dockerfile: imagen `python:3.11-slim`, instala deps del proyecto y expone `uvicorn`.
- Compose: `docker-compose.yml` con healthcheck y variables (`.env.example`).
