#!/bin/bash
# Script para procesar todos los documentos con CLI y extraer los .corrections.docx

CORRECCIONES_DIR="correcciones"
OUTPUT_DIR="correcciones_finales"
TEMP_OUTPUT="temp_cli_outputs"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$TEMP_OUTPUT"

cd "$(dirname "$0")/.."

echo "[BATCH] Procesando $(ls "$CORRECCIONES_DIR"/*.docx 2>/dev/null | wc -l) documentos..."

count=0
for docx in "$CORRECCIONES_DIR"/*.docx; do
    [ -f "$docx" ] || continue

    count=$((count + 1))
    filename=$(basename "$docx")
    echo "[$count] Procesando: $filename"

    # Ejecutar corrección
    python -m corrector.cli "$docx" --out "$TEMP_OUTPUT/${filename%.docx}.corrected.docx" --log "$TEMP_OUTPUT/${filename%.docx}.jsonl" --log-docx "$TEMP_OUTPUT/${filename%.docx}.corrections.docx" --auto-chunk

    # Mover solo el archivo de correcciones al output final
    if [ -f "$TEMP_OUTPUT/${filename%.docx}.corrections.docx" ]; then
        cp "$TEMP_OUTPUT/${filename%.docx}.corrections.docx" "$OUTPUT_DIR/"
        echo "    [OK] Guardado en $OUTPUT_DIR/${filename%.docx}.corrections.docx"
    fi
done

echo ""
echo "[DONE] Procesados $count documentos"
echo "       Archivos en: $OUTPUT_DIR/"
ls -1 "$OUTPUT_DIR"/*.corrections.docx 2>/dev/null | wc -l | xargs echo "       Total:"
