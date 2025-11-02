# Feature: Aceptación/Rechazo de Correcciones

## Descripción

Sistema completo para gestionar la aceptación o rechazo de correcciones sugeridas por el corrector, permitiendo al usuario tener control granular sobre qué cambios se aplican al documento final.

## Características Principales

### 1. Persistencia de Sugerencias

Cada corrección detectada se almacena como un registro `Suggestion` en la base de datos con:
- **Estado** (`status`): `pending`, `accepted`, `rejected`
- **Clasificación**: tipo (ortografía, puntuación, estilo, léxico, etc.) y severidad
- **Contexto**: texto original, reemplazo sugerido, razón, contexto y frase completa
- **Trazabilidad**: token_id, línea, fuente (regla o IA), confianza

### 2. Gestión Individual y por Lotes

**Operaciones individuales:**
- Ver detalles de una corrección específica
- Aceptar o rechazar una corrección individual

**Operaciones por lotes:**
- Aceptar/rechazar múltiples correcciones seleccionadas
- Aceptar/rechazar todas las correcciones pendientes de un run

### 3. Filtrado y Consulta

- Listar todas las correcciones de un run
- Filtrar por estado (pending, accepted, rejected)
- Ordenar por token_id para mantener el orden del documento

### 4. Exportación Selectiva

Generar el documento final con **solo las correcciones aceptadas**:
- Preserva el formato original del documento
- Aplica únicamente las correcciones con estado `accepted`
- Mantiene la integridad del texto mediante el sistema de tokens

## Arquitectura

### Flujo de Datos

```
1. Procesamiento del documento
   ↓
2. Generación de LogEntry por cada corrección
   ↓
3. Persistencia como Suggestion (status=pending)
   ↓
4. Usuario revisa y acepta/rechaza
   ↓
5. Generación de documento final con correcciones aceptadas
```

### Modelo de Datos

**Tabla `suggestions`:**
```python
class Suggestion(SQLModel, table=True):
    id: str                           # UUID
    run_id: str                       # FK a Run
    document_id: str                  # FK a Document
    token_id: int                     # ID del token en el documento
    line: int                         # Número de línea
    suggestion_type: SuggestionType   # ortografia, puntuacion, concordancia, estilo, lexico
    severity: SuggestionSeverity      # error, warning, info
    before: str                       # Texto original
    after: str                        # Texto sugerido
    reason: str                       # Explicación
    source: SuggestionSource          # rule o llm
    confidence: float                 # 0.0-1.0 (para IA)
    context: str                      # Contexto (tokens cercanos)
    sentence: str                     # Frase completa
    status: SuggestionStatus          # pending, accepted, rejected
    created_at: datetime
```

### Endpoints API

**Base URL:** `/suggestions`

#### Listar Sugerencias
```http
GET /suggestions/runs/{run_id}/suggestions?status=pending
```
Retorna todas las sugerencias de un run, opcionalmente filtradas por estado.

#### Ver Sugerencia Individual
```http
GET /suggestions/suggestions/{suggestion_id}
```

#### Actualizar Estado Individual
```http
PATCH /suggestions/suggestions/{suggestion_id}
Content-Type: application/json

{
  "status": "accepted"  // o "rejected"
}
```

#### Actualización por Lotes
```http
POST /suggestions/runs/{run_id}/suggestions/bulk-update
Content-Type: application/json

{
  "suggestion_ids": ["uuid1", "uuid2", ...],
  "status": "accepted"
}
```

#### Aceptar Todas
```http
POST /suggestions/runs/{run_id}/suggestions/accept-all
```

#### Rechazar Todas
```http
POST /suggestions/runs/{run_id}/suggestions/reject-all
```

#### Exportar con Correcciones Aceptadas
```http
POST /suggestions/runs/{run_id}/export-with-accepted
```
Retorna el documento en formato DOCX con solo las correcciones aceptadas aplicadas.

## Implementación

### 1. Worker (`server/worker.py`)

El worker ahora:
1. Procesa el documento usando `process_paragraphs()` para obtener `LogEntry` objects
2. Persiste cada `LogEntry` como un `Suggestion` con estado `pending`
3. Clasifica automáticamente el tipo basado en palabras clave en el motivo
4. Mantiene compatibilidad con exports JSONL/DOCX/CSV existentes

**Clasificación automática:**
```python
# Ejemplo de clasificación por palabras clave
if "ortografía" in reason_lower:
    suggestion_type = SuggestionType.ortografia
elif "puntuación" in reason_lower:
    suggestion_type = SuggestionType.puntuacion
elif "léxico" or "confusión" in reason_lower:
    suggestion_type = SuggestionType.lexico
```

### 2. Rutas (`server/routes_suggestions.py`)

Nuevo router con todos los endpoints de gestión de sugerencias:
- Verificación de permisos (usuario debe ser dueño del run)
- Validación de estados
- Generación de documento final con tokenización

### 3. Generación de Documento Final

```python
# 1. Obtener sugerencias aceptadas
accepted = session.exec(
    select(Suggestion)
    .where(Suggestion.run_id == run_id,
           Suggestion.status == SuggestionStatus.accepted)
    .order_by(Suggestion.token_id)
).all()

# 2. Tokenizar documento original
paragraphs = read_paragraphs(input_path)
tokens = tokenize("\n".join(paragraphs))

# 3. Aplicar solo correcciones aceptadas
corrected_tokens = apply_token_corrections(tokens, accepted)

# 4. Generar documento preservando formato
write_docx_preserving_runs(input_path, corrected_paragraphs, output_path)
```

## Casos de Uso

### Caso 1: Revisor Editorial

1. Ejecuta un run de corrección sobre un capítulo
2. Obtiene lista de 150 sugerencias
3. Revisa las primeras 20 de tipo "ortografía" y las acepta todas
4. Filtra por tipo "estilo" y rechaza 5 que no se ajustan al tono
5. Exporta documento con solo las 145 correcciones aceptadas

### Caso 2: Autor Indie

1. Ejecuta corrección en modo "Rápido"
2. Acepta todas las correcciones de ortografía automáticamente
3. Revisa manualmente las de estilo
4. Exporta versión final

### Caso 3: Editorial con Políticas Específicas

1. Ejecuta corrección en modo "Profesional"
2. Filtra por severidad "error" y acepta todas
3. Filtra por tipo "lexico" y revisa manualmente
4. Rechaza sugerencias que contradicen guía de estilo interna
5. Exporta documento limpio

## Beneficios

✅ **Control granular**: El usuario decide qué correcciones aplicar
✅ **Trazabilidad completa**: Cada decisión queda registrada
✅ **Workflow eficiente**: Operaciones por lotes para productividad
✅ **Integración con IA**: Clasificación automática de sugerencias
✅ **Formato preservado**: El documento final mantiene todo el formato original
✅ **Auditoría**: Historial completo de sugerencias y decisiones

## Extensiones Futuras

- **Aprendizaje de preferencias**: Detectar patrones en aceptaciones/rechazos del usuario
- **Reglas personalizadas**: "Siempre aceptar tipo X, siempre rechazar tipo Y"
- **Comentarios en sugerencias**: Permitir al usuario añadir notas
- **Comparación visual**: UI para ver antes/después con resaltado
- **Track changes en export**: Generar DOCX con cambios marcados para revisión en Word
- **Multi-documento**: Aplicar decisiones de un documento a otros similares

## Migración y Compatibilidad

La funcionalidad es **completamente retrocompatible**:
- Los logs JSONL/CSV existentes siguen generándose
- El documento `.corrected.docx` con todas las correcciones se mantiene
- La nueva tabla `suggestions` se agrega sin afectar tablas existentes
- El endpoint de export adicional es opt-in

## Testing

### Pruebas Básicas

```bash
# 1. Ejecutar corrección (genera sugerencias)
curl -X POST http://localhost:8000/runs \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"project_id": "...", "documents": ["..."]}'

# 2. Listar sugerencias
curl http://localhost:8000/suggestions/runs/{run_id}/suggestions \
  -H "Authorization: Bearer $TOKEN"

# 3. Aceptar una corrección
curl -X PATCH http://localhost:8000/suggestions/suggestions/{suggestion_id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "accepted"}'

# 4. Exportar con aceptadas
curl -X POST http://localhost:8000/suggestions/runs/{run_id}/export-with-accepted \
  -H "Authorization: Bearer $TOKEN" \
  -o documento_final.docx
```

### Casos de Prueba

1. ✅ Persistencia: Verificar que todas las correcciones se guardan como `Suggestion`
2. ✅ Estados: Cambiar estado de pending → accepted → rejected
3. ✅ Filtrado: Filtrar por estado y tipo
4. ✅ Bulk operations: Aceptar/rechazar múltiples
5. ✅ Export: Verificar que solo las aceptadas se aplican
6. ✅ Formato: Confirmar preservación de formato en export
7. ✅ Permisos: Verificar que solo el owner puede modificar
8. ✅ Token alignment: Confirmar que token_id se mantiene consistente

## Documentación para Desarrolladores

### Agregar Nuevo Tipo de Sugerencia

```python
# 1. Actualizar enum en server/models.py
class SuggestionType(str, Enum):
    # ... existentes
    nuevo_tipo = "nuevo_tipo"

# 2. Actualizar clasificación en worker._persist_suggestions()
if any(kw in reason_lower for kw in ["palabra_clave1", "palabra_clave2"]):
    suggestion_type = SuggestionType.nuevo_tipo
```

### Extender API de Sugerencias

Todos los endpoints están en `server/routes_suggestions.py`. Para añadir funcionalidad:

```python
@router.post("/suggestions/custom-operation")
def custom_operation(
    run_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # 1. Verificar permisos
    run = session.get(Run, run_id)
    if not run or run.submitted_by != current_user.id:
        raise HTTPException(status_code=403)

    # 2. Tu lógica aquí
    ...
```

---

**Versión:** 1.0
**Última actualización:** 2025-11-02
**Autor:** Sistema de Corrección
