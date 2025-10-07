# Frontend Progress Checklist

- [x] Paleta y estilos base (ink/teal/red/paper) en Tailwind.
- [x] Scaffold SPA (Vite + React + TS) en `web/`.
- [x] Visor JSONL offline con modos Inline/Stacked/Side.
- [x] API client Axios + React Query.
- [x] Rutas: `/`, `/projects`, `/projects/:id`, `/runs/:runId`.
- [x] Backend FastAPI MVP: health, projects, upload, runs, artifacts.
- [x] Dockerización dev (`docker-compose.dev.yml`).
- [x] Dockerización prod (`docker-compose.yml`).
- [x] Listado/creación de proyectos (UI + API).
- [x] Subida múltiple de documentos (UI + API).
- [x] Lanzar run y ver artefactos (UI + API, polling).
- [x] Integrar visor CorrectionsTable con API (cargar JSONL remoto).
- [ ] Filtros por severidad/tipo y chips (cuando backend exponga campos).
- [ ] Stepper y Dropzone drag&drop.
- [ ] Autenticación (guest/usuario) y límites por plan.
- [ ] SSE/WebSocket para progreso en tiempo real.
- [ ] Visor DOCX (track changes) embebido o descarga mejorada.
- [ ] CI/CD y previsualizaciones (PRs) del frontend.
