# Plan de Implementación — Core Functionality Diferenciadora

Basado en `docs/market-analysis.md`, este plan se enfoca en las funcionalidades núcleo que nos diferencian del mercado: edición de “libro largo” en español con trazabilidad total, procesamiento por lotes, memoria de proyecto, normas conmutables con citas (RAE/DPD) y exportables con evidencia. Se excluyen detalles específicos de backend y frontend; se crearán documentos dedicados.

## Principios de Diseño
- Español primero (es‑ES y es‑MX en MVP), con variaciones conmutables por proyecto.
- Profundidad editorial y trazabilidad: cada cambio tiene motivo, contexto, regla/autoridad y reversibilidad.
- Pipeline híbrido reglas + IA, siempre auditable y degradable a solo reglas.
- Pensado para libro largo: proyecto, capítulos, consistencia intercapítulos y re‑ejecuciones idempotentes.
- Privacidad y confianza: opción de no entrenar con textos, preparación para self‑host/on‑prem.

## Funcionalidades Núcleo (Scope MVP extendido)

### 1) Procesamiento por Lotes y Memoria de Proyecto
- Ingesta de múltiples archivos (capítulos) en un “proyecto” con metadatos (idioma, variante, estilo, glosario).
- Memoria de decisiones (p. ej., grafías preferidas, tratamientos, toponimia, nombres propios) aplicada de forma consistente en todo el proyecto.
- Re‑ejecución incremental: solo difs desde el último run; control de versiones de reglas/modelos.
- Artefactos reproducibles: `project.yaml` (config), `run.json` (parámetros), `changelog.csv` (resultados), `summary.md` (carta editorial).
- Aceptación: ejecutar un proyecto de 100k–150k palabras en <30 min en modo “Rápido” con logs por línea.

### 2) Motor Híbrido Reglas+IA con Normas Conmutables
- Reglas deterministas en español con severidad/códigos y cita de fuente (RAE/DPD/Fundéu cuando aplique).
- Paquetes de reglas conmutables: `Ortografía`, `Puntuación`, `Concordancia`, `Estilo general`, `Regionalismos es‑ES/es‑MX`.
- IA generativa para reescrituras guiadas (claridad, tono, formalidad) con explicación breve y límites de cambios.
- Trazabilidad: cada sugerencia indica `source=rule|llm`, `rule_id/model_id`, confianza y contexto (frase/párrafo).
- Aceptación: ≥80% de sugerencias “aceptables” en corpora gold internos (medido por revisión editorial).

### 3) Registro Detallado de Cambios (per‑línea) y Exportables
- `changelog` estructurado por token/frase con: tipo, severidad, descripción, antes/después, motivo, cita normativa, ubicación (doc, capítulo, offset), fuente y confianza.
- Filtros por tipo/severidad/archivo; agregados por capítulo y por proyecto.
- Exportables: `CSV` para auditoría y `JSONL` para análisis; API interna para enriquecer informes.
- Aceptación: round‑trip consistente entre logs y representaciones en DOCX (track changes) con <1% de desalineación de offsets en manuscritos típicos.

### 4) Exportador DOCX con Track Changes + Carta Editorial
- Import preservando estilos/citas/notas al pie; export con `track changes` y comentarios (razón/cita abreviada).
- “Carta de edición” (`summary.md`) con: principales categorías de errores, decisiones de estilo, checklist de consistencia y próximos pasos.
- Aceptación: apertura en Word/Google Docs sin alertas; aplicabilidad selectiva de cambios (Aceptar/Rechazar) manteniendo formato.

### 5) Inspector de Consistencia (tipo PerfectIt, para español)
- Chequeos intercapítulos: guionización, mayúsculas, numerales, abreviaturas, uso de cursivas/comillas, listas de personajes/glosario.
- Reglas parametrizables por proyecto y reportes con ejemplos representativos y “arreglar todo” seguro.
- Aceptación: detección de ≥95% de inconsistencias configuradas en corpus de prueba; falsos positivos <10% en categorías críticas.

### 6) Diccionario/Glosario de Proyecto y Guía de Estilo
- Diccionario de equipo (nombres propios, tecnicismos, preferidos/evitados) con validación en tiempo de análisis.
- Guía de estilo por proyecto: decisiones (p. ej., “solo” tildado/no tildado), formatos numéricos, tratamiento de tuteo/ustedeo, localismos permitidos, época/registro (p. ej., castellano clásico vs. contemporáneo) y rasgos de personajes (voz/idiolecto, nivel de formalidad, tics lingüísticos) aplicables por capítulo/escena.
- Aceptación: aplicación consistente en todo el proyecto y reflejo en carta editorial.

### 7) Modos de Uso: “Rápido” y “Profesional”
- Rápido: corrección automática + carta de edición, sin configuración profunda; pensado para autores indie.
- Profesional: logs detallados, configuración de paquetes de reglas, glosario y consistencia; pensado para editoriales.
- Aceptación: tiempos objetivo (Rápido <30 min; Profesional <90 min para 120k palabras) en hardware estándar.

### 8) Privacidad y Despliegue (Base)
- Políticas: “no entrenamos con tus textos” por defecto; retención y borrado controlados por proyecto.
- Preparación para self‑host/on‑prem: separación clara de componentes con alternativas “solo reglas”.
- Aceptación: auditoría básica de datos en repos de proyecto; switches de telemetría y salida sin datos sensibles.

### 9) Detección de Idioma y Auto‑Inferencia de Estilo (Premium)
- Detección automática de idioma/variante por documento y proyecto (es‑ES/es‑MX, señalando mezclas) con heurísticos + modelo ligero local.
- Auto‑perfil de estilo (premium): inferir tono, registro, comillas preferidas, puntuación, tratamiento (tú/usted), tildado de “solo”, leísmo, formato numérico, marcas de época y regionalismos a partir de muestreos estratificados del manuscrito.
- Auto‑perfil de personajes (premium): extracción de “tarjetas” por personaje a partir de diálogos y narración cercana (voz, formalidad, muletillas) con sugerencias de consistencia.
- Control de presupuesto IA: chunking seguro (páginas representativas, diálogos, primeras/últimas secciones) y límites por proyecto/usuario.
- Aceptación: perfiles útiles en ≥80% de casos (validados por editora), con opción de revisión/edición manual y versionado.

## Roadmap de Entregas (6–8 semanas)

- Semana 1–2: Fundaciones proyecto/lote, data model, importador DOCX/TXT, `changelog` básico y export CSV/JSONL.
- Semana 3–4: Paquetes de reglas es‑ES/es‑MX con citas; inspector de consistencia inicial; carta editorial inicial.
- Semana 5–6: Export DOCX con track changes estable; memoria de proyecto (diccionario + estilo); modos Rápido/Profesional.
- Semana 7–8: IA para reescrituras explicadas; métricas de calidad; limpieza de DX (config YAML, re‑ejecución incremental) y hardening.

## Métricas de Éxito (MVP)
- Calidad: ≥80% aceptación editorial en pruebas ciegas; falsos positivos críticos <10%.
- Trazabilidad: 100% de sugerencias con motivo/cita o justificación IA; exportables consistentes.
- Productividad: reducción ≥40% del tiempo de primera pasada en manuscritos de 100k palabras.
- Confiabilidad: 0 fallos de apertura en DOCX exportados en Word/Docs en pruebas de regresión.

## Fuera de Alcance (MVP)
- Integraciones con Scrivener/Word como add‑ins, LMS u otras plataformas.
- Edición creativa (estructura narrativa profunda) más allá de tips agregados.
- Analíticas avanzadas multiusuario y dashboarding.

## Dependencias y Suposiciones
- Corpora de prueba en español (es‑ES/es‑MX) con “truth set” editorial.
- Referencias normativas (RAE/DPD/Fundéu) para justificación de reglas.
- Capacidad de ejecutar IA de forma controlada (o modo degradado a solo reglas cuando no disponible).

---

Este plan se alinea con el resumen estratégico del análisis de mercado: edición de libro largo en español con trazabilidad total, batch, memoria de proyecto, normas conmutables con citas y logs exportables.
