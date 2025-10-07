# AGENTS Guide: Progreso y Mantenimiento de Checklists

Este archivo define convenciones para mantener actualizados los checklists de progreso y, cuando corresponda, reflejar avances en el `README.md`.

Alcance: este archivo aplica a todo el repositorio.

## Archivos de progreso
- `progress/backend-checklist.md`: tareas del backend (API, datos, colas, despliegue, seguridad, etc.).
- `progress/core-checklist.md`: tareas del core funcional (motor, reglas, exportadores, consistencia, estilo, etc.).
- `progress/frontend-checklist.md`: tareas del frontend (rutas, componentes, integración API, Dockerización).

## Reglas de mantenimiento
- Siempre que completes o avances una tarea relacionada, actualiza el checklist correspondiente en el mismo cambio (patch/PR):
  - Marca con `[x]` los ítems completados.
  - Añade nuevos ítems con `[ ]` cuando surjan tareas relevantes.
  - Mantén cada ítem en una sola línea, conciso y accionable.
- Si el avance es visible para personas usuarias (p. ej., nuevos endpoints, subidas reales, exportables), añade o ajusta una nota breve en la sección “Progreso” del `README.md` enlazando al ítem.
- No dupliques información extensa: los detalles pertenecen a los planes en `docs/` y al código. Los checklists reflejan estado y próximos pasos.

### Frontend: documentación y checklist obligatorios
- Cualquier cambio en `web/` o `docker-compose*.yml` debe:
  - Actualizar `docs/frontend-plan.md` si modificas alcance, rutas, o UX de alto nivel.
  - Actualizar `progress/frontend-checklist.md` marcando tareas y añadiendo nuevas si aplica.
- Incluye en el PR un resumen breve del impacto en el plan/checklist.

## Estilo de los checklists
- Secciones con encabezados breves; ítems con `- [ ]` o `- [x]`.
- Incluye referencias útiles (archivo, endpoint) cuando aporte claridad.
- Evita anidar listas; un ítem por línea.

## Flujo sugerido
1) Actualiza código y tests.
2) Marca el/los ítem(s) como `[x]` en `progress/*.md` y añade nuevos si procede.
3) Actualiza `README.md` (sección “Progreso”) solo si afecta al uso o a la comunicación externa.
