¡Muy buena idea! Ya existe mucha “oferta horizontal” de correctores, pero hay huecos interesantes—sobre todo en español y en flujos editoriales de libro largo—que tu enfoque (batch + registro detallado de cambios con motivo y contexto) podría cubrir muy bien. Abajo te dejo:

* **un mapa del mercado (qué hace cada quién, con foco en español y en obra larga);**
* **oportunidades y nichos poco atendidos;**
* **una propuesta de MVP diferenciador (en 4–6 semanas de desarrollo realista) y siguientes pasos de validación.**

---

## 1) Mapa rápido del mercado (2025)

**A. Generalistas “todo‑terreno”**

* **Grammarly.** Acaba de añadir soporte para español, francés, portugués, alemán e italiano con corrección gramatical, reescrituras a nivel de párrafo y traducción en línea. Movimiento muy reciente (sept. 2025). Fuerte en UX e integraciones, débil históricamente en edición “de libro” / flujos por capítulos. ([Grammarly](https://www.grammarly.com/blog/company/grammarly-launches-multilingual-support/?utm_source=chatgpt.com "Grammarly Launches Multilingual Writing Support | Grammarly Blog"))
* **LanguageTool.** Multilingüe con buen soporte para español y dialectos; ofrece **Style Guide** y **Team Dictionary** para normas personalizadas; núcleo **open‑source** con posibilidad de **auto‑hospedado** (privacidad). ([LanguageTool](https://languagetool.org/insights/post/product-languages-supported/?utm_source=chatgpt.com "LanguageTool: A Multilingual Spelling and Grammar Checker"))
* **DeepL Write.** En 2024 amplió idioma y hoy ofrece español en Write/Write Pro con corrección y ajuste de estilo/tono. Fuerte percepción de calidad lingüística. ([DeepL](https://www.deepl.com/en/en/es/en/blog/deepl-write-welcomes-french-spanish?utm_source=chatgpt.com "DeepL Write: your AI-powered writing assistant now ... - DeepL Translate"))
* **Microsoft Editor / Google Docs.** Soporte de español integrado (Word, Docs) y sugerencias de estilo básicas; conveniencia alta, pero sin informes profundos ni “memoria de proyecto”. ([Microsoft Support](https://support.microsoft.com/en-us/office/editor-s-spelling-grammar-and-refinement-availability-by-language-ecd60e9f-6b2e-4070-b30c-42efa6cff55a?utm_source=chatgpt.com "Editor's spelling, grammar, and refinement availability by language"))
* **QuillBot / Wordtune.** Parafraseo y gramática con soporte en español (especialmente QuillBot); orientadas a snippets, no a proyectos largos ni a trazabilidad editorial. ([help.quillbot.com](https://help.quillbot.com/hc/en-us/articles/4541525640727-What-languages-does-QuillBot-work-in?utm_source=chatgpt.com "What languages does QuillBot work in? – QuillBot Help Center"))

**B. Herramientas para autores de ficción / libro largo**

* **ProWritingAid.** Integración con  **Scrivener** ; informes de manuscrito (estructura, capítulos, “Virtual Beta Reader”). No es específicamente español, pero marca la pauta de “análisis de manuscrito” y del  **flujo por proyecto** . ([help.prowritingaid.com](https://help.prowritingaid.com/article/330-using-manuscript-analysis-with-scrivener?utm_source=chatgpt.com "Using Manuscript Analysis or Virtual Beta Reader with Scrivener"))
* **AutoCrit / Fictionary.** Métricas de ritmo, diálogo, clichés, arcos de personaje, etc. (desarrollo de historia más que corrección gramatical). ([Kindlepreneur](https://kindlepreneur.com/autocrit-review/?utm_source=chatgpt.com "Autocrit Review [2025]: Read This Before Purchasing - Kindlepreneur"))

**C. Herramientas para editores profesionales (consistencia / normas)**

* **PerfectIt.** “Inspector de consistencia” en Word con hojas de estilo (incluye integración con  **Chicago Manual of Style** ). Gran referencia en flujos editoriales —pero centrado en inglés. ([The Chicago Manual of Style Online](https://www.chicagomanualofstyle.org/help-tools/perfectit.html?utm_source=chatgpt.com "The Chicago Manual of Style® for PerfectIt"))
* **WordRake.** Reescritura por claridad/brevedad en Word/Outlook con  **track changes** ; domina jurídico/negocios en inglés. ([wordrake.com](https://www.wordrake.com/?utm_source=chatgpt.com "Writing Assistant for Professionals | WordRake Editing Software"))
* **Antidote.** Corrector+diccionarios+guías (inglés/francés; **offline** disponible). No cubre español, lo que abre hueco. ([antidote.info](https://www.antidote.info/en/antidote-plus?utm_source=chatgpt.com "Antidote+: Three Applications, One Subscription"))

**D. “Made in español”**

* **Stilus.** Complemento para Word, revisa ortografía/gramática/estilo **con referencias normativas** (RAE, Fundéu y otras autoridades). Fuerte anclaje normativo, menos foco en proyecto de libro y trazabilidad por lote. ([Appsource – Business Apps](https://appsource.microsoft.com/es-es/product/office/WA200003400?utm_source=chatgpt.com "Stilus for Word"))
* **Correcto** (startup). Corrector/reescritura centrado en español para negocio/marketing. ([correcto](https://www.correctoai.com/?utm_source=chatgpt.com "Herramienta de IA para mejorar tu comunicación - Correcto"))

**E. Linters y pipelines (per‑línea, exportable)**

* **Vale** /  **proselint** : linters de prosa (CLI), config por reglas y salida con  **línea/archivo/regla** , ideales para **logs de auditoría** y CI. Poca UX “de autor”, enorme trazabilidad. ([vale.sh](https://vale.sh/?utm_source=chatgpt.com "Vale: Your style, our editor"))

---

## 2) ¿Qué está bien cubierto y qué no?

**Cubierto (competencia fuerte):**

* Corrección “al vuelo” en apps (Grammarly, LanguageTool, Editor). ([Grammarly](https://www.grammarly.com/blog/company/grammarly-launches-multilingual-support/?utm_source=chatgpt.com "Grammarly Launches Multilingual Writing Support | Grammarly Blog"))
* Parafraseo y ajuste de tono a nivel frase/párrafo. ([DeepL](https://www.deepl.com/en/features/write?utm_source=chatgpt.com "The AI writing assistant | DeepL Write Pro"))
* Informes de alto nivel para novela (estructura, ritmo)  **en inglés** . ([ProWritingAid](https://prowritingaid.com/features/manuscript-analysis?utm_source=chatgpt.com "Manuscript Analysis | ProWritingAid's AI Book Reviewer"))

**Infra‑atendido / con huecos claros (oportunidad):**

1. **Libro largo en español con “memoria de proyecto”:** residuos de consistencia (nombres, tuteo/voseo, mayúsculas, guiones, cifras) a lo largo de 90–120k palabras siguen siendo dolorosos. PerfectIt lo resuelve en inglés; en español hay menos oferta “de proyecto”. ([support.perfectit.com](https://support.perfectit.com/kb/guide/en/quickstart-perfectit-for-word-windows-WH5RSIAgBQ/Steps/2426482?utm_source=chatgpt.com "Quickstart - PerfectIt for Word (Windows) | PerfectIt Customer ..."))
2. **Logs auditables por línea con motivo y fuente normativa:** pocos productos generan **CSV/JSON** con `capítulo/posición → sugerencia → regla → justificación → referencia (RAE/DPD)`. Stilus referencia normas, pero no expone un log de auditoría granular tipo linter. ([mystilus.es](https://mystilus.es/referencias-linguisticas?utm_source=chatgpt.com "Autoridades lingüísticas | Stilus"))
3. **Modos normativos configurables (RAE/DPD vs. inclusivo/guía corporativa):** necesidad de alternar **“estricto académico”** (RAE/DPD) frente a **“guía inclusiva”** de una institución, con reglas conmutables y justificaciones. (DPD/RAE e iniciativas de lenguaje inclusivo sirven como base de reglas). ([Real Academia Española](https://www.rae.es/obras-academicas/diccionarios/diccionario-panhispanico-de-dudas-0?utm_source=chatgpt.com "Diccionario panhispánico de dudas - Real Academia Española"))
4. **Privacidad/“on‑prem” y procesado por lotes:** editoriales y autores valoran no subir manuscritos a la nube. Un backend auto‑hospedado al estilo LanguageTool + motor LLM controlado es diferenciador. ([LanguageTool](https://languagetool.org/dev?utm_source=chatgpt.com "Open Source - LanguageTool"))
5. **Export editorial “plug‑and‑play”:** DOCX con **track changes** + **informe de edición** + **hoja de estilo** automática (glosario de personajes/lugares, decisiones de mayúsculas, etc.). Hoy hay piezas (p. ej., Trinka permite descargar DOCX con cambios; PWA da informes), pero no una solución integral en español con logs justificables. ([trinka.ai](https://www.trinka.ai/features/proofread-file?utm_source=chatgpt.com "Automatic Grammar Correction for your MS Word file with Trinka"))

---

## 3) Propuesta de posicionamiento (“nicho defendible”)

**“El primer corrector de manuscritos en español con trazabilidad editorial completa.”**

* **Batch real de libro** (DOCX/MD/EPUB) con **memoria de proyecto** (nombres, estilo, variantes regionales).
* **Registro por línea** con **código de regla y referencia** (p. ej.,  *DPD: dequeísmo* ), exportable a **CSV/JSON** y consultable en UI. ([Real Academia Española](https://www.rae.es/obras-academicas/diccionarios/diccionario-panhispanico-de-dudas-0?utm_source=chatgpt.com "Diccionario panhispánico de dudas - Real Academia Española"))
* **Modos de norma conmutables** :
* *RAE/DPD estricto* (con citas a DLE/DPD). ([Diccionario Español Tricentenario](https://dle.rae.es/?utm_source=chatgpt.com "Diccionario de la lengua española | Edición del Tricentenario | RAE - ASALE"))
* *Inclusivo configurable* (guías internas, Fundéu/otras). ([MJusticia](https://www.mjusticia.gob.es/es/AreaTematica/DocumentacionPublicaciones/InstListDownload/Guia%20lenguaje%20inclusivo.pdf?utm_source=chatgpt.com "Guía para el uso de un lenguaje más inclusivo e igualitario"))
* *Voz del autor* (con “frases protegidas” y umbral de agresividad).
* **Privado/auto‑hospedado** (para editoriales) + **SDK/CLI** (para integrarlo en CI). Basado en un analizador tipo **LanguageTool self‑hosted** + reglas propias y tu capa LLM para reescrituras y explicaciones. ([dev.languagetool.org](https://dev.languagetool.org/http-server.html?utm_source=chatgpt.com "LanguageTool embedded HTTP Server | dev.languagetool.org"))

---

## 4) MVP sugerido (en 4 bloques funcionales)

1. **Ingesta & proyecto**
   * Arrastra carpeta (capítulos .docx/.md/.txt).
   * Detección de **entidades** (personajes, lugares, términos) y **hoja de estilo** inicial. (Inspirado en la “consistency” de PerfectIt, pero para español). ([support.perfectit.com](https://support.perfectit.com/kb/guide/en/quickstart-perfectit-for-word-windows-WH5RSIAgBQ/Steps/2426482?utm_source=chatgpt.com "Quickstart - PerfectIt for Word (Windows) | PerfectIt Customer ..."))
2. **Corrección por lotes con log explicable**
   * Pipeline híbrido: **reglas deterministas** (laísmo/leísmo/dequeísmo; tildes diacríticas; signos) + **LLM** para fluidez.
   * **Salida triple** :
   * **DOCX** con *track changes* (como hace Trinka, validando la entrega que espera un editor). ([trinka.ai](https://www.trinka.ai/features/proofread-file?utm_source=chatgpt.com "Automatic Grammar Correction for your MS Word file with Trinka"))
   * **CSV/JSON de auditoría** (`archivo, línea, texto original, sugerencia, regla, referencia, confianza`).
   * **Informe de edición** (resumen de categorías, % aceptadas, riesgos).
3. **Normas conmutables y multi‑variante**
   * Perfiles:  **es‑ES** ,  **es‑MX** ,  **es‑AR** , etc.; toggles de  *tuteo/voseo/ustedeo* ; preferencia de comillas (« » / “ ”) y guiones de diálogo.
   * **Modo RAE/DPD** con citas a entradas pertinentes (DLE/DPD) para cada sugerencia relevante. ([Diccionario Español Tricentenario](https://dle.rae.es/?utm_source=chatgpt.com "Diccionario de la lengua española | Edición del Tricentenario | RAE - ASALE"))
   * **Modo inclusivo** : recomendaciones y alternativas (desdoblamientos, opciones no marcadas), con referencias a guías institucionales. ([MJusticia](https://www.mjusticia.gob.es/es/AreaTematica/DocumentacionPublicaciones/InstListDownload/Guia%20lenguaje%20inclusivo.pdf?utm_source=chatgpt.com "Guía para el uso de un lenguaje más inclusivo e igualitario"))
4. **Memoria de proyecto & coherencia**
   * Panel de **consistencias** (nombres, capitalización, ortotipografía, numerales) y **glosario** exportable (lo que en edición se llama “hoja de estilo”).
   * Integraciones: **Scrivener** (como demanda probada por ProWritingAid),  **Word** , **Google Docs** (complementos). ([help.prowritingaid.com](https://help.prowritingaid.com/article/330-using-manuscript-analysis-with-scrivener?utm_source=chatgpt.com "Using Manuscript Analysis or Virtual Beta Reader with Scrivener"))

> **Tecnología base recomendada:** combinar **LanguageTool self‑hosted** (API local para reglas y detección robusta en español), un **módulo de reglas propias** (YAML/XML al estilo Vale) y tu **LLM (Gemini 2.5 Flash)** para reescrituras/explanations  *cortas y estructuradas* , no “pensamiento en voz alta” (cumple políticas y da mejor trazabilidad). ([dev.languagetool.org](https://dev.languagetool.org/http-server.html?utm_source=chatgpt.com "LanguageTool embedded HTTP Server | dev.languagetool.org"))

---

## 5) “Moats” (defensas) frente a gigantes

* **Trazabilidad de nivel editorial (per‑línea con norma citada)** : hoy casi nadie lo hace con esta granularidad; lo más parecido son linters de prosa (Vale/proselint) pero sin UX de autor ni enfoque español. ([vale.sh](https://vale.sh/?utm_source=chatgpt.com "Vale: Your style, our editor"))
* **Privacidad y on‑prem por defecto** , algo que editoriales y autoras valoran; pocos generalistas ofrecen un camino tan claro (LanguageTool sí permite self‑host, pero sin capa de proyecto/libro ni informes cerrados). ([LanguageTool](https://languagetool.org/dev?utm_source=chatgpt.com "Open Source - LanguageTool"))
* **Norma española “conmutables”** (RAE/DPD vs. inclusivo) con  **citas** : Stilus referencia autoridades, pero no entrega un **paquete editor + hoja de estilo + log** sobre proyectos de 100k palabras. ([mystilus.es](https://mystilus.es/referencias-linguisticas?utm_source=chatgpt.com "Autoridades lingüísticas | Stilus"))

---

## 6) Métricas/funciones que enamoran a autoras de novela (y a editores)

* **Panel de ritmo y diálogo** (densidad por capítulo, varianza de longitudes, uso de adverbios, exclamaciones). Funcionalidad tipo AutoCrit, adaptada al español. ([Kindlepreneur](https://kindlepreneur.com/autocrit-review/?utm_source=chatgpt.com "Autocrit Review [2025]: Read This Before Purchasing - Kindlepreneur"))
* **Detector de “ismos”** (dequeísmo, queísmo, laísmo/leísmo/loísmo) con ejemplos y citas RAE/DPD. ([Real Academia Española](https://www.rae.es/obras-academicas/diccionarios/diccionario-panhispanico-de-dudas-0?utm_source=chatgpt.com "Diccionario panhispánico de dudas - Real Academia Española"))
* **Concordancia y tiempos verbales** a largo documento (no solo oraciones aisladas).
* **Protección de voz** : lista de **frases/personajes** “intocables” y umbral de intervención.
* **Export “editor‑ready”** : DOCX con cambios + **Edit Letter** + **Hoja de estilo** + **CSV de auditoría** (para auditorías internas o trabajo con coeditores). ([trinka.ai](https://www.trinka.ai/features/proofread-file?utm_source=chatgpt.com "Automatic Grammar Correction for your MS Word file with Trinka"))

---

## 7) Validación rápida en el mercado (en 2–3 semanas)

1. **Landing y lista de espera** con la promesa: *“Corrección de manuscritos en español con log auditable y normas conmutables (RAE/DPD ↔ inclusivo), en local o nube privada.”*
   * Público:  **autoras indie** , **editoriales pequeñas/median** y  **servicios de corrección** .
2. **Pilotos** con 5–10 manuscritos (70–120k palabras) de distintos países (es‑ES/es‑MX/es‑AR).
3. **Benchmark** frente a: Grammarly (nuevo español), LanguageTool, Stilus y ProWritingAid (para estructura), midiendo:
   * % de problemas de consistencia inter‑capítulo detectados,
   * precisión en “ismos”,
   * **tiempo ahorrado** y  **aceptación de cambios** ,
   * utilidad del **log** para justificar decisiones editoriales. ([Grammarly](https://www.grammarly.com/blog/company/grammarly-launches-multilingual-support/?utm_source=chatgpt.com "Grammarly Launches Multilingual Writing Support | Grammarly Blog"))

---

## 8) Modelo de negocio sugerido

* **Indie** (autoras): pago **por proyecto** (p. ej., hasta 120k palabras) + add‑ons (segunda pasada, “edit letter” extendida).
* **Profesional/Editorial** : **SaaS seats** + **on‑prem** (licencia anual) + **reglas personalizadas** / implantación (servicios).
* **Diferenciador contractual** : tratamiento de datos “no entrenamos con tus textos”, alineado con lo que comunica ProWritingAid para tranquilizar al mercado. ([Kindlepreneur](https://kindlepreneur.com/prowritingaid-manuscript-analysis/?utm_source=chatgpt.com "ProWritingAid's Manuscript Analysis: What It Is (&amp; How It Works)"))

---

## 9) Riesgos y cómo mitigarlos

* **Entrada de Grammarly en español.** Contrarresta con *profundidad editorial* (logs, norma citada, on‑prem) y  *libro largo* . ([Grammarly](https://www.grammarly.com/blog/company/grammarly-launches-multilingual-support/?utm_source=chatgpt.com "Grammarly Launches Multilingual Writing Support | Grammarly Blog"))
* **Complejidad UX.** Ofrece  **dos modos** : *“Rápido”* (corrección + carta de edición) y *“Profesional”* (logs, reglas finas).
* **Cobertura normativa y variación regional.** Arranca con es‑ES y es‑MX + reglas de alta frecuencia; añade variantes por telemetría y feedback (reglas como “paquetes”, al estilo Vale/Style Guide). ([LanguageTool](https://languagetool.org/insights/post/style-guide/?utm_source=chatgpt.com "LanguageTool’s Style Guide Helps Your Team Stay Cohesive"))

---

## 10) Resumen Ejecutivo (en una frase)

 **Tu ventaja competitiva** : llevar al español **la edición de libro larga con trazabilidad total** — **batch** ,  **memoria de proyecto** , **norma conmutables con citas (RAE/DPD)** y **logs per‑línea** exportables— algo que los grandes correctores no priorizan y que editores/autorías necesitan para trabajar con seguridad y justificar cambios. ([Real Academia Española](https://www.rae.es/obras-academicas/diccionarios/diccionario-panhispanico-de-dudas-0?utm_source=chatgpt.com "Diccionario panhispánico de dudas - Real Academia Española"))

---

### Fuentes clave (selección)

* Grammarly añade español y más idiomas (sept. 2025). ([Grammarly](https://www.grammarly.com/blog/company/grammarly-launches-multilingual-support/?utm_source=chatgpt.com "Grammarly Launches Multilingual Writing Support | Grammarly Blog"))
* LanguageTool en español, Style Guide y opción self‑host. ([LanguageTool](https://languagetool.org/insights/post/product-languages-supported/?utm_source=chatgpt.com "LanguageTool: A Multilingual Spelling and Grammar Checker"))
* DeepL Write/Write Pro con español. ([DeepL](https://www.deepl.com/en/en/es/en/blog/deepl-write-welcomes-french-spanish?utm_source=chatgpt.com "DeepL Write: your AI-powered writing assistant now ... - DeepL Translate"))
* ProWritingAid Manuscript Analysis y uso con Scrivener. ([ProWritingAid](https://prowritingaid.com/features/manuscript-analysis?utm_source=chatgpt.com "Manuscript Analysis | ProWritingAid's AI Book Reviewer"))
* PerfectIt + Chicago Manual of Style (consistencia en Word). ([The Chicago Manual of Style Online](https://www.chicagomanualofstyle.org/help-tools/perfectit.html?utm_source=chatgpt.com "The Chicago Manual of Style® for PerfectIt"))
* Stilus (español, autoridades RAE/Fundéu). ([mystilus.es](https://mystilus.es/referencias-linguisticas?utm_source=chatgpt.com "Autoridades lingüísticas | Stilus"))
* Linters de prosa (Vale/proselint) para trazabilidad por línea. ([vale.sh](https://vale.sh/?utm_source=chatgpt.com "Vale: Your style, our editor"))
* Trinka (ejemplo de exportar  **DOCX con track changes** ). ([trinka.ai](https://www.trinka.ai/features/proofread-file?utm_source=chatgpt.com "Automatic Grammar Correction for your MS Word file with Trinka"))

---

Si te encaja, puedo bosquejar **la especificación técnica** del pipeline (reglas deterministas + LLM + exportadores DOCX/CSV + CLI) y un **roadmap** de 90 días con hitos de validación comercial.
