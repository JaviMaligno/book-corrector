"""Test manual para verificar correcciones."""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

from corrector.docx_utils import read_paragraphs
from corrector.engine import process_document
from corrector.model import GeminiCorrector
from corrector.prompt import load_base_prompt

# Paths
sample = Path("tests/samples/gemini_live_input.docx")
out_doc = Path("output_test.docx")
log_json = Path("log_test.jsonl")

# Clean old files
if out_doc.exists():
    out_doc.unlink()
if log_json.exists():
    log_json.unlink()

print("=" * 80)
print("PROCESANDO DOCUMENTO CON GEMINI")
print("=" * 80)

base_prompt = load_base_prompt()
corrector = GeminiCorrector(base_prompt_text=base_prompt)

process_document(
    str(sample),
    str(out_doc),
    str(log_json),
    corrector,
    chunk_words=0,
    overlap_words=0,
    preserve_format=True,
    enable_docx_log=False,
)

print("\n" + "=" * 80)
print("DOCUMENTO CORREGIDO:")
print("=" * 80)
out_paragraphs = read_paragraphs(str(out_doc))
for i, p in enumerate(out_paragraphs, 1):
    print(f"{i}. {p}")

print("\n" + "=" * 80)
print("LOG DE CORRECCIONES:")
print("=" * 80)

if log_json.exists():
    content = log_json.read_text(encoding="utf-8")
    if content.strip():
        lines = [ln for ln in content.splitlines() if ln.strip()]
        print(f"Total de correcciones: {len(lines)}")
        for line in lines:
            entry = json.loads(line)
            print(f"\n  Original: '{entry.get('original', 'N/A')}'")
            print(f"  Corrección: '{entry.get('correction', 'N/A')}'")
            print(f"  Razón: {entry.get('reason', 'N/A')}")
    else:
        print("⚠️  El archivo de log está vacío")
else:
    print("❌ El archivo de log no existe")

print("\n" + "=" * 80)
print("VALIDACIÓN:")
print("=" * 80)

out_text = "\n".join(out_paragraphs)

# Verificar que los nombres propios están presentes
if "María" in out_text:
    print("✓ 'María' presente en el texto")
else:
    print("✗ 'María' NO encontrada")

if "Barcelona" in out_text:
    print("✓ 'Barcelona' presente en el texto")
else:
    print("✗ 'Barcelona' NO encontrada")

# Verificar que se corrigió vello → bello
if "bello" in out_text and "vello" not in out_text:
    print("✓ 'vello' fue corregido a 'bello'")
elif "vello" in out_text:
    print("✗ 'vello' NO fue corregido (todavía aparece en el texto)")
else:
    print("? No se encontró ni 'vello' ni 'bello'")
