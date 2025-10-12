# Plan Unificado de UI/Frontend

Este documento consolida el plan existente del frontend (docs/frontend-plan.md) y el diseño de UI en un plan único, exhaustivo y accionable. Cubre flujos, componentes, datos, endpoints y entregables para la revisión interactiva, la visualización de artefactos y la exportación de feedback.

## 0) Estado del arte (resumen)
- Acciones masivas: Grammarly agrupa sugerencias de alta confianza; LanguageTool aplica “todas de este tipo”; PerfectIt tiene “Fix All” con cautela.
- Presentación habitual: subrayados inline + panel lateral, sin vista comparada completa.
- Oportunidad: vista comparada original↔corregido a escala de manuscrito con motivo y cita (RAE/DPD) + log exportable y aplicable.

## 1) Objetivos UX y alcance
- Subir, revisar y aplicar cambios en 3–4 pasos con feedback claro.
- Dos modos: Rápido (auto‑aplicación segura) y Profesional (control fino por regla/categoría/confianza).
- Diferenciadores: tri‑panel (lista → comparado → motivo), citación normativa y dataset de feedback exportable.

## 2) Arquitectura y Rutas
- Stack: Vite + React + TypeScript + Tailwind + TanStack Query.
- Utilidades FE: `diff-match-patch` o `jsdiff` para dif fino; `react-virtual` para listas largas; `zustand`/Context para estado de revisión.
- Rutas: `/` (Visor JSONL), `/projects`, `/projects/:id`, `/runs/:runId`, `/runs/:runId/review`.
- API: FastAPI; endpoints de proyectos, upload, runs, artifacts y nuevos endpoints de revisión (sección 6).

## 3) Flujos y Pantallas
- Tabla de Correcciones (Vista Principal)
  - **Diseño tipo DOCX**: Tabla profesional con columnas: # | Frase Completa | Original → Corregido | Motivo | Línea
  - **Frase completa de contexto**: Mostrar la frase entera donde ocurre la corrección (campo `sentence`), NO solo 3 tokens alrededor
  - **Resaltado inline**: Dentro de la frase, resaltar en rojo tachado el texto original y en verde el texto corregido
  - **Búsqueda y filtros**: Por palabra, motivo, categoría, tipo de error
  - **Vistas alternativas**: Inline (por defecto), Antes/Después (apilado), Lado a lado
  - **Enlace a revisión**: Botón para entrar en modo revisión interactiva
- Proyectos y Runs
  - Proyectos: creación/listado; detalle con subida múltiple y "Corregir".
  - RunDetail: estado con polling y enlaces; salto a tabla de correcciones o `/runs/:runId/review` si existen `*.corrections.jsonl`.
- Revisión (tri‑panel) - Futuro
  - Lista/tabla filtrable (regla, categoría, documento, confianza, estado).
  - Comparado con scroll sincronizado: original (izq) vs corregido (der) y vista inline en contexto.
  - Panel lateral: motivo, explicación breve, referencia (RAE/DPD/Fundéu), confianza y acciones Aceptar/Rechazar.
  - Barras: superior con contadores (aceptadas/rechazadas/pendientes), toggle "Aceptar por defecto", botones "Aceptar/Rechazar restantes"; inferior con navegación y atajos (A/R/U).

## 4) Componentes (FE)
- Existentes: `CorrectionsTable`, `ContextSnippet` (extender con selección y dif fino).
- Nuevos: `ReviewProvider` (estado decisiones, defaultAccept, filtros), `ReviewList` (virtualizada), `ReviewSidePanel` (detalle), `ReviewActionsBar` (bulk/contadores), `ReviewPreview` (previsualización local o de backend).

## 5) Interacción y Acciones
- Aceptar/Rechazar por corrección; atajos: A (aceptar), R (rechazar), U (undo); navegación ↑/↓.
- Bulk por categoría/regla/documento/umbral de confianza; “aceptar por defecto” + “aceptar/rechazar restantes”.
- Perfiles de auto‑aplicación: Seguro (orto/espacios/signos) vs Revisar (estilo/reescritura); previsualización antes de aplicar.
- Historial/undo por lote y reinicio de sesión de revisión.

## 6) Datos e Integración Backend
- **Formato JSONL de correcciones** (`*.corrections.jsonl`):
  ```json
  {
    "token_id": 2,
    "line": 1,
    "original": "baca",
    "corrected": "vaca",
    "reason": "Confusión baca/vaca (techo del coche)",
    "context": "La baca del",        // 3 tokens alrededor (legacy)
    "sentence": "La baca del coche estaba llena de equipaje.",  // FRASE COMPLETA (nuevo campo requerido)
    "chunk_index": 0,
    "suggestion_id": "abc123",       // hash estable (futuro)
    "category": "confusión léxica",  // categoría de error (futuro)
    "confidence": 0.95               // confianza del modelo (futuro)
  }
  ```
- **Extracción de sentence** (Backend):
  - En `engine.py`, antes de guardar cada corrección, extraer la frase completa donde ocurre el error
  - Usar delimitadores de frase: `.`, `!`, `?`, `;`, o `\n\n`
  - Buscar hacia atrás y adelante desde `token_id` hasta encontrar inicio/fin de frase
  - Almacenar en campo `sentence` del JSONL
- Identificadores estables por sugerencia: `suggestion_id` (hash de `doc_id|token_id|original|corrected|rule_id`), `token_id`, `sentence`, offsets si hay.
- Modelo de revisión (futuro)
  - `review_sessions(id, run_id, user_id, default_accept, created_at)`.
  - `review_decisions(id, session_id, suggestion_id, action, created_at)` con `action ∈ {accept,reject,unset}`.
- Endpoints propuestos (futuro)
  - `GET /runs/{id}/suggestions` → JSON (o servir `*.corrections.jsonl`) con `suggestion_id`, `rule_id`, `category`, `confidence`.
  - `POST /runs/{id}/reviews` → guardar/actualizar decisiones (array de `{suggestion_id, action}`).
  - `POST /runs/{id}/reviews/bulk` → aplicar por filtros (`category`, `rule_id`, `confidence_min`, `doc_id`, `state=pending`).
  - `GET /runs/{id}/preview` → documento temporal con decisiones aplicadas (HTML/TXT o DOCX).
  - `POST /runs/{id}/finalize` → exportable final (`*.final.corrected.docx`) y registro en `exports`.
  - `GET /runs/{id}/reviews/export` → dataset JSONL/CSV (ver 8) con anonimización opcional.

## 7) Aplicación de Decisiones (apply)
- Algoritmo determinista por `token_id` y orden en `sentence`; resolver solapamientos conservando contexto.
- “Dry run” (previsualización) y “apply” (persistencia/export) diferenciados; idempotencia por `suggestion_id`.

## 8) Dataset de Feedback y Fine‑tuning
- Registro por evento: `project_id`, `doc_id`, `segment_id|sentence`, `original`, `suggested`, `corrected`, `rule_id`, `category`, `reference_url`, `confidence_model`, `action_user (accept|reject|edit)`, `edit_text?`, `locale`, `timestamp`.
- SFT (instruccional): pares input/output solo de `accept|edit`.
- Preferencias: pares aceptada vs rechazada en mismo contexto para rankers/clasificadores.
- Gemini 2.5 Flash: no FT directo vía API; emplear few‑shot/RAG. Para FT, usar OSS (Llama/Mistral) con LoRA/QLoRA offline y opt‑in.
- Privacidad: anonimizar PII, políticas por proyecto, opt‑in y borrado.

## 9) Priorización de Reglas (MVP)
| Categoría | Regla / Caso | Auto‑aplicar | Mostrar revisión |
| --- | --- | --- | --- |
| 🟢 Ortografía básica | Tildes diacríticas (tú/tu, él/el) | ✅ | Opcional |
| 🟢 Tipografía | Espacios dobles, comillas rectas→tipográficas | ✅ | Opcional |
| 🟢 Signos | Falta de punto, espacio antes de coma | ✅ | Opcional |
| 🟡 Gramática | Dequeísmo, leísmo, concordancia verbal | ⚠️ | ✅ |
| 🟡 Estilo | Muletillas, redundancias | ❌ | ✅ |
| 🔴 Reescrituras | Reformulaciones completas | ❌ | ✅ (confianza ≥ 0.8) |

## 10) Roadmap y Entregables
- **S1 (MVP actual)**:
  - ✅ Base SPA, paleta básica, rutas de proyectos y runs
  - 🔄 **Backend**: Añadir campo `sentence` (frase completa) al JSONL en `engine.py`
  - 🔄 **Frontend**: Tabla de correcciones tipo DOCX con frase completa y resaltado inline
  - 🔄 **Integración**: `RunDetail` muestra enlace a tabla de correcciones por run
- **S2**: Mejoras de tabla
  - Búsqueda y filtros avanzados (por palabra, motivo, categoría)
  - Vistas alternativas (Inline, Antes/Después, Lado a lado)
  - Exportar tabla a PDF o DOCX con formato
- **S3**: UI de Revisión tri‑panel (A/R individual, panel lateral, filtros, atajos, scroll sincronizado, lista virtualizada)
- **S4**: Persistencia en backend de decisiones; `preview`/`finalize`; bulk por filtros; export dataset
- **S5**: Perfiles de auto‑aplicación, umbral de confianza, undo/redo por lote; mejoras UX; SSE/WebSocket opcional

## 11) Pruebas, Rendimiento y Observabilidad
- FE: pruebas de componentes (diff, panel), accesibilidad básica, smoke e2e (carga JSONL, A/R, preview).
- BE: tests de endpoints de revisión, idempotencia, aplicación determinista y export de dataset.
- Rendimiento: virtualización de listas >10k sugerencias; pre‑cálculo de diffs pesados; streaming de preview.
- Observabilidad: contadores por sesión (aplicadas/rechazadas), tiempos y errores por regla.

## 12) Dependencias y Herramientas
- FE: `react`, `typescript`, `vite`, `tailwind`, `@tanstack/react-query`, `jsdiff`/`diff-match-patch`, `react-virtual`, `zustand`/Context.
- BE: FastAPI, SQLModel/SQLite, endpoints en `server/routes_runs.py` y/o nuevo router `routes_reviews.py`, `python-docx`/exportador DOCX.

## 13) Riesgos y Mitigaciones
- Identificadores inestables en logs → fijar `suggestion_id` (hash) y `token_id`.
- Aplicación incorrecta en solapamientos → ordenar por offsets, validar post‑aplicación.
- UX de “aceptar todo” → barandillas (perfiles/umbral/dry‑run) y undo por lote.

