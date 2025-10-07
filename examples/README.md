# Ejemplos de Uso

## Ejemplo Básico

Para probar el corrector con el documento de ejemplo:

```bash
# Corregir el documento de muestra
python -m corrector.cli tests/samples/gemini_live_input.docx

# Los archivos generados estarán en outputs/:
# - outputs/gemini_live_input.corrected.docx  (documento corregido)
# - outputs/gemini_live_input.corrections.jsonl  (log JSON)
# - outputs/gemini_live_input.corrections.docx  (informe con tabla)
```

## Colocar tus Documentos

Puedes colocar tus documentos `.docx` en esta carpeta `examples/` para organizarlos mejor:

```bash
# Copiar tu documento
cp ~/Documentos/mi_texto.docx examples/

# Corregirlo
python -m corrector.cli examples/mi_texto.docx

# Ver resultados
ls -l outputs/mi_texto.*
```

## Casos de Uso

### 1. Corrección Simple

```bash
python -m corrector.cli mi_documento.docx
```

### 2. Sin Generar Informe DOCX

```bash
python -m corrector.cli mi_documento.docx --no-log-docx
```

### 3. Especificar Rutas Personalizadas

```bash
python -m corrector.cli entrada.docx \
  --out corregido.docx \
  --log mis_correcciones.jsonl \
  --log-docx informe.docx
```

### 4. Usar Modelo Diferente

```bash
python -m corrector.cli documento.docx --model gemini-2.5-pro
```

### 5. Modo Local (Sin API)

Para pruebas rápidas sin consumir API:

```bash
python -m corrector.cli documento.docx --local-heuristics
```

## Ejemplos de Errores Detectados

El corrector es especialmente bueno detectando:

- **Tildes faltantes**: `rio` → `rió`, `hablo` → `habló`
- **Confusiones léxicas**: `vello` → `bello`, `baca` → `vaca`
- **Gerundio vs Participio**: `contemplado` → `contemplando`
- **Homófonos**: `hojear` ↔ `ojear`, `vaya` ↔ `valla`

## Personalización

Para ajustar el comportamiento del corrector:

1. **Editar el prompt**: Modifica `docs/base-prompt.md`
2. **Ajustar chunking**: Usa `--chunk-words` para documentos muy largos
3. **Cambiar modelo**: La variable `GEMINI_MODEL` en `.env`
