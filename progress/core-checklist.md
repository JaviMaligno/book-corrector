# Checklist — Core Functionality

Estado del core diferenciador (motor, reglas, exportables, consistencia, estilo). Mantener actualizado según AGENTS.md.

## Batch y memoria de proyecto
- [ ] Artefactos reproducibles por run: `project.yaml`, `run.json`, `changelog.csv`, `summary.md`
- [ ] Re‑ejecución incremental (diffs desde último run) y versionado de reglas/modelos
- [ ] Memoria de decisiones (grafías, tratamiento, toponimia) aplicada en todo el proyecto

## Motor híbrido (reglas + IA)
- [ ] Reglas deterministas en español con severidad/códigos y citas (RAE/DPD/Fundéu)
- [ ] Paquetes de reglas: Ortografía, Puntuación, Concordancia, Estilo general, Regionalismos (es‑ES/es‑MX)
- [ ] Reescrituras con IA con explicación breve y límites (premium)

## Logs y exportables
- [x] Log JSONL por corrección (token_id, línea, motivo, contexto) — `corrector/engine.py`
- [ ] Exportador CSV a partir del log
- [ ] Alineación <1% entre log y DOCX con track changes

## DOCX + carta editorial
- [ ] Export DOCX con track changes y comentarios (razón/cita)
- [ ] Carta editorial (`summary.md`) con métricas, decisiones y checklist
- [x] Informe DOCX tipo tabla (no track changes) ya disponible

## Inspector de consistencia
- [ ] Chequeos intercapítulos: guionización, mayúsculas, numerales, abreviaturas, itálicas/comillas, personajes/glosario
- [ ] Reporte con ejemplos y opción de “arreglar todo” seguro

## Diccionario/Glosario y guía de estilo
- [ ] Diccionario de equipo (preferidos/evitados) con validación
- [ ] Guía de estilo por proyecto: “solo” tildado, números, tratamiento, localismos, época/registro y rasgos de personajes

## Modos de uso
- [ ] Modo Rápido (auto + carta) y Profesional (logs detallados y configuración fina) parametrizados en `Run.mode`

## Detección y auto‑inferencia (premium)
- [ ] Detección automática de idioma/variante (es‑ES/es‑MX)
- [ ] Auto‑perfil de estilo y personajes por chunking estratificado y prompts estructurados

## Privacidad y rendimiento
- [ ] Política “no entrenamos con tus textos”, retención/borrado por proyecto y redacción en prompts
- [ ] Benchmark: 100k–150k palabras en <30 min (Rápido)

## Interoperabilidad
- [ ] Exportables (CSV/JSONL/MD) consumibles por backend y descargables vía API

