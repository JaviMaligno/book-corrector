"""Script para diagnosticar el problema de corrección de Gemini con logs detallados."""

import sys
from pathlib import Path

# Configurar UTF-8 en Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from corrector.docx_utils import read_paragraphs
from corrector.model import GeminiCorrector
from corrector.prompt import build_json_prompt, load_base_prompt
from corrector.text_utils import tokenize

# Leer el archivo de entrada
sample = Path(__file__).resolve().parent / "tests" / "samples" / "gemini_live_input.docx"
paragraphs = read_paragraphs(str(sample))

print("=" * 80)
print("CONTENIDO DEL ARCHIVO:")
print("=" * 80)
for i, p in enumerate(paragraphs, 1):
    print(f"{i}. {p}")

# Tokenizar
full_text = "\n".join(paragraphs)
tokens = tokenize(full_text)

print("\n" + "=" * 80)
print("TOKENS GENERADOS:")
print("=" * 80)
for i, token in enumerate(tokens[:50]):  # Mostrar primeros 50 tokens
    print(f"{i}: {token.kind:8} | {repr(token.text)}")
if len(tokens) > 50:
    print(f"... ({len(tokens) - 50} tokens más)")

# Cargar prompt base
base_prompt = load_base_prompt()
print("\n" + "=" * 80)
print("PROMPT BASE:")
print("=" * 80)
print(base_prompt)

# Construir el prompt final
final_prompt = build_json_prompt(base_prompt, tokens)
print("\n" + "=" * 80)
print("PROMPT FINAL ENVIADO A GEMINI:")
print("=" * 80)
print(final_prompt)

# Crear corrector y ejecutar
print("\n" + "=" * 80)
print("EJECUTANDO CORRECCIÓN CON GEMINI...")
print("=" * 80)
corrector = GeminiCorrector(base_prompt_text=base_prompt)

try:
    corrections = corrector.correct_tokens(tokens)

    print(f"\nCORRECCIONES ENCONTRADAS: {len(corrections)}")
    print("=" * 80)
    if corrections:
        for corr in corrections:
            print(f"Token ID: {corr.token_id}")
            print(f"  Original: {corr.original or '(no especificado)'}")
            print(f"  Reemplazo: {corr.replacement}")
            print(f"  Razón: {corr.reason}")
            print()
    else:
        print("⚠️  No se encontraron correcciones")
        print("\nEsto puede deberse a:")
        print("1. El prompt es demasiado genérico")
        print("2. Gemini no detecta los errores de confusión")
        print("3. El formato de respuesta JSON no es el esperado")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
print("ANÁLISIS:")
print("=" * 80)
print("Errores esperados en el texto:")
print("1. 'vello' → 'bello' (el paisaje era realmente vello)")
print("   Contexto: paisaje (estético)")
print("\nNota: 'baca' es CORRECTO en 'La baca del coche' (portaequipajes)")
print("      'ojear' es CORRECTO en 'ojear el libro' (mirar rápidamente)")
