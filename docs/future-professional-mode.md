# Modo Profesional - Visión Futura en Modelo Freemium

## Estado Actual

**Nota**: Esta funcionalidad NO está implementada actualmente. Este documento describe la visión futura para un modo profesional diferenciado dentro del modelo freemium del corrector.

El campo `mode` existe en la base de datos pero no tiene efecto en el comportamiento del sistema. Actualmente, todos los usuarios reciben el mismo nivel de correcciones (ortografía y léxico con IA Gemini).

## Visión: Modo Profesional

El **Modo Profesional** sería una característica premium que ofrece correcciones más avanzadas y especializadas, más allá de ortografía y gramática básica.

### Objetivo

Proporcionar un nivel de corrección editorial profesional que incluya análisis de estilo, coherencia textual, y verificación de normas especializadas para diferentes tipos de documentos.

---

## Diferenciación: Modo Gratuito vs. Profesional

### Modo Gratuito (Plan Free)

**Alcance básico:**
- ✅ Corrección ortográfica
- ✅ Detección de confusiones léxicas (vaca/baca, haya/halla)
- ✅ Puntuación básica (comas, puntos, signos de interrogación)
- ✅ Concordancia básica (género y número)
- ❌ Sin análisis de estilo
- ❌ Sin reglas especializadas por tipo de documento
- ❌ Sin verificación de consistencia terminológica

**Límites:**
- 1 corrección simultánea
- 1 documento por ejecución
- Sin prioridad en cola

### Modo Profesional (Plan Premium)

**Alcance avanzado:**
- ✅ Todo lo del modo gratuito
- ✅ **Análisis de estilo editorial**
  - Detección de redundancias
  - Sugerencias de simplificación sintáctica
  - Identificación de muletillas y clichés
  - Análisis de longitud de oraciones
  - Detectar voz pasiva excesiva
- ✅ **Coherencia y cohesión textual**
  - Verificación de conectores lógicos
  - Detección de repeticiones a distancia
  - Consistencia de tiempos verbales
  - Análisis de progresión temática
- ✅ **Reglas especializadas por tipo de documento**
  - Académico: Verificar formato APA/MLA/Chicago
  - Legal: Verificar lenguaje jurídico normativo
  - Técnico: Consistencia terminológica y glosario
  - Literario: Respeto de voz narrativa y estilo autoral
  - Corporativo: Tono profesional y lenguaje claro
- ✅ **Verificación de consistencia terminológica**
  - Glosario del proyecto (términos preferidos)
  - Detección de variantes terminológicas
  - Sugerencias basadas en corpus especializado
- ✅ **Normas y referencias citables**
  - Citas de diccionarios normativos (RAE, DPD, Fundéu)
  - Referencias a manuales de estilo
  - Justificación lingüística de cada sugerencia

**Límites:**
- 2 correcciones simultáneas
- 3 documentos por ejecución
- Prioridad alta en cola

---

## Implementación Técnica Propuesta

### 1. Prompt Diferenciado

**Modo Gratuito** (actual):
```
Corrige ortografía, puntuación básica y confusiones léxicas comunes.
Devuelve solo errores evidentes.
```

**Modo Profesional** (futuro):
```
Actúa como editor profesional. Además de ortografía y gramática:
1. Analiza estilo editorial (redundancias, muletillas, longitud de oraciones)
2. Verifica coherencia textual (conectores, tiempos verbales)
3. Aplica reglas del tipo de documento: {document_type}
4. Consulta glosario del proyecto: {project_glossary}
5. Cita normas relevantes (RAE, DPD, manual de estilo)

Clasifica cada sugerencia:
- ortografia: Errores ortográficos evidentes
- lexico: Confusiones léxicas
- estilo: Mejoras de estilo editorial
- coherencia: Problemas de cohesión textual
- terminologia: Inconsistencias terminológicas

Devuelve solo correcciones justificadas con citas normativas cuando aplique.
```

### 2. Tipo de Documento y Perfil de Estilo

**Modelo de datos ampliado:**

```python
class DocumentType(str, Enum):
    general = "general"
    academic = "academic"
    legal = "legal"
    technical = "technical"
    literary = "literary"
    corporate = "corporate"

class StyleProfile(SQLModel, table=True):
    id: str
    project_id: str
    document_type: DocumentType
    style_rules: str  # JSON con reglas específicas
    glossary: str  # JSON con términos preferidos
    tone: str  # "formal", "informal", "technical"
    person: str  # "first", "third", "impersonal"
    citations_enabled: bool = True
```

**Ejemplo de uso:**

```python
# Usuario configura perfil de estilo para proyecto académico
style_profile = StyleProfile(
    project_id="abc-123",
    document_type=DocumentType.academic,
    style_rules=json.dumps({
        "max_sentence_length": 35,
        "passive_voice_tolerance": 0.1,
        "citation_style": "APA7",
        "avoid_first_person": True
    }),
    glossary=json.dumps({
        "inteligencia artificial": "IA (preferido)",
        "machine learning": "aprendizaje automático"
    }),
    tone="formal",
    person="impersonal"
)
```

### 3. Pipeline de Corrección Ampliado

**Arquitectura de múltiples capas:**

```python
def correct_document_professional(doc, style_profile):
    corrections = []

    # Layer 1: Ortografía y gramática básica (ambos modos)
    corrections += orthographic_layer(doc)

    if mode == "profesional":
        # Layer 2: Análisis de estilo editorial
        corrections += style_analysis_layer(doc, style_profile)

        # Layer 3: Coherencia textual
        corrections += coherence_layer(doc)

        # Layer 4: Verificación terminológica
        corrections += terminology_layer(doc, style_profile.glossary)

        # Layer 5: Normas citables
        corrections = enrich_with_citations(corrections)

    return corrections
```

### 4. Sugerencias con Citas Normativas

**Modelo ampliado:**

```python
class Suggestion(SQLModel, table=True):
    # ... campos existentes ...
    citation_id: str | None  # FK a catálogo normativo
    citation_text: str | None  # Texto de la cita
    citation_source: str | None  # "RAE", "DPD", "Fundéu"

class NormativeCatalog(SQLModel, table=True):
    id: str
    source: str  # "RAE", "DPD", "Fundéu", "Manual APA"
    ref: str  # Referencia específica
    title: str
    snippet: str  # Extracto relevante
```

**Ejemplo de sugerencia con cita:**

```json
{
  "before": "el Internet",
  "after": "internet",
  "reason": "El sustantivo 'internet' se escribe con minúscula inicial",
  "citation_source": "RAE",
  "citation_text": "internet. [...] Se escribe con inicial minúscula.",
  "citation_ref": "https://dle.rae.es/internet"
}
```

---

## Beneficios del Modelo Freemium

### Para Usuarios Gratuitos
- ✅ Acceso a correcciones esenciales sin costo
- ✅ Evaluar calidad del servicio antes de pagar
- ✅ Suficiente para documentos personales básicos

### Para Usuarios Premium
- 💎 Correcciones de nivel editorial profesional
- 💎 Ahorro de tiempo en revisión manual
- 💎 Consistencia terminológica en proyectos grandes
- 💎 Justificación normativa para cada decisión editorial
- 💎 Personalización por tipo de documento

### Para el Negocio
- 💰 Conversión natural de free → premium al ver valor
- 💰 Diferenciación clara de valor agregado
- 💰 Costos de IA distribuidos (free usa menos tokens)
- 💰 Escalabilidad sostenible

---

## Casos de Uso Premium

### 1. Tesis Doctoral
**Necesidades:**
- Consistencia terminológica en 300+ páginas
- Formato APA estricto
- Tono académico impersonal
- Sin muletillas ni redundancias

**Valor del Modo Profesional:**
- Detección de variantes terminológicas ("aprendizaje automático" vs "machine learning")
- Verificación de formato de citas
- Sugerencias de simplificación sintáctica sin perder formalidad
- Reporte de consistencia de voz narrativa

### 2. Contrato Legal
**Necesidades:**
- Lenguaje jurídico normativo
- Precisión terminológica crítica
- Evitar ambigüedades
- Referencias a código legal

**Valor del Modo Profesional:**
- Glosario jurídico especializado
- Detección de términos ambiguos
- Sugerencias de formulaciones estándar
- Verificación de consistencia en definiciones

### 3. Manual Técnico Corporativo
**Necesidades:**
- Terminología técnica consistente
- Tono profesional claro
- Instrucciones sin ambigüedad
- Glosario corporativo

**Valor del Modo Profesional:**
- Aplicación de glosario corporativo personalizado
- Detección de inconsistencias técnicas
- Simplificación de lenguaje técnico sin perder precisión
- Verificación de estructura de documentación

### 4. Novela Literaria
**Necesidades:**
- Respeto de voz autoral
- Detección de repeticiones no intencionales
- Consistencia de nombres y lugares
- Sugerencias sutiles de estilo

**Valor del Modo Profesional:**
- Detección de repeticiones a distancia (no solo léxicas)
- Análisis de ritmo narrativo
- Respeto de licencias estilísticas (no marcar como error)
- Sugerencias opcionales sin imponer estilo

---

## Estrategia de Comunicación

### Mensaje Principal
> "Modo Profesional: Más allá de ortografía, un editor profesional en tu equipo"

### Diferenciadores Clave en Marketing
1. **"No solo corrige, mejora tu escritura"**
   - Free: Corrige errores
   - Pro: Mejora estilo y claridad

2. **"Citas normativas en cada sugerencia"**
   - Free: Te dice qué está mal
   - Pro: Te explica por qué y cita la norma

3. **"Adapta las reglas a tu tipo de documento"**
   - Free: Reglas generales
   - Pro: Reglas especializadas (académico, legal, técnico)

4. **"Consistencia terminológica en proyectos grandes"**
   - Free: Documento por documento
   - Pro: Glosario del proyecto, detección de variantes

### Pricing Sugerido
- **Free**: $0/mes (correcciones básicas, 1 doc/vez)
- **Premium**: $19/mes (modo profesional, 3 docs/vez, prioridad)
- **Profesional**: $49/mes (todo lo anterior + API access, 10 docs/vez)

---

## Roadmap de Implementación

### Fase 1: MVP Diferenciado (2-3 meses)
- [ ] Prompts diferenciados (básico vs profesional)
- [ ] Clasificación automática de sugerencias por tipo
- [ ] Tipo de documento configurable en proyecto
- [ ] UI para mostrar clasificación de sugerencias

### Fase 2: Estilo y Coherencia (2-3 meses)
- [ ] Análisis de estilo editorial (redundancias, longitud de oraciones)
- [ ] Detección de coherencia textual básica
- [ ] Perfil de estilo por proyecto
- [ ] Reglas específicas por tipo de documento

### Fase 3: Glosario y Terminología (1-2 meses)
- [ ] Glosario del proyecto (CRUD de términos)
- [ ] Detección de variantes terminológicas
- [ ] Sugerencias basadas en glosario
- [ ] Importar/exportar glosario

### Fase 4: Citas Normativas (2 meses)
- [ ] Catálogo normativo básico (RAE, DPD, Fundéu)
- [ ] Enriquecimiento de sugerencias con citas
- [ ] UI para mostrar citas en sugerencias
- [ ] Links a fuentes normativas

### Fase 5: Optimización y Escalado (continuo)
- [ ] A/B testing de prompts
- [ ] Caché de sugerencias comunes
- [ ] Optimización de costos de IA
- [ ] Análisis de conversión free → premium

---

## Consideraciones Técnicas

### Costos de IA
**Modo Gratuito:**
- Prompt más corto (~500 tokens)
- Solo correcciones básicas
- Estimado: $0.02 por documento (1000 palabras)

**Modo Profesional:**
- Prompt más largo con contexto (~2000 tokens)
- Análisis multicapa
- Consulta a glosario y catálogo normativo
- Estimado: $0.08 por documento (1000 palabras)

**Sostenibilidad:**
- Free: Subsidia adquisición, costos bajos
- Premium: Cubre costos + margen
- A $19/mes, con ~500 docs/mes → ROI positivo

### Performance
- Modo Gratuito: ~30-60s por documento (1000 palabras)
- Modo Profesional: ~60-120s por documento (análisis multicapa)
- Paralelización: Mantener 2 workers por modo para no degradar experiencia

---

## Métricas de Éxito

### Conversión
- **Objetivo**: 5-10% conversión free → premium al mes 3
- **Indicador**: Usuarios free que corrijan >5 docs en una semana

### Retención Premium
- **Objetivo**: >70% retención mensual
- **Indicador**: Cancelaciones por mes

### Satisfacción
- **Objetivo**: NPS >40 en usuarios premium
- **Indicador**: Encuesta post-corrección

### Valor Percibido
- **Objetivo**: >60% de usuarios premium usan todas las funciones pro
- **Indicador**: % que configuran glosario, ven citas normativas

---

## Conclusión

El **Modo Profesional** no es solo un "modo más lento" o "con más reglas", sino un **salto cualitativo en el tipo de asistencia editorial** que ofrece el corrector:

- **Modo Gratuito**: Corrector automático de errores evidentes
- **Modo Profesional**: Asistente editorial que mejora claridad, estilo y consistencia

Esta diferenciación clara justifica el modelo freemium y crea un camino natural de conversión cuando los usuarios necesitan correcciones más sofisticadas o trabajan en proyectos profesionales donde la calidad editorial es crítica.

---

## Referencias

- [Pricing freemium best practices](https://www.priceintelligently.com/blog/freemium-pricing-strategy)
- [Grammarly's freemium model](https://www.grammarly.com/plans)
- [RAE - Diccionario panhispánico de dudas](https://www.rae.es/dpd/)
- [Fundéu - Manual de estilo](https://www.fundeu.es/)
