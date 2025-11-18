"""Script para ver la respuesta RAW de Gemini."""

import json
import sys
from pathlib import Path

# Configurar UTF-8 en Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from corrector.docx_utils import read_paragraphs
from corrector.llm import get_gemini_client
from corrector.model import CorrectionsResponse, _build_tools_from_pydantic, _extract_function_call
from corrector.prompt import build_json_prompt, load_base_prompt
from corrector.text_utils import tokenize

# Leer el archivo de entrada
sample = Path(__file__).resolve().parent / "tests" / "samples" / "gemini_live_input.docx"
paragraphs = read_paragraphs(str(sample))
full_text = "\n".join(paragraphs)
tokens = tokenize(full_text)

# Cargar prompt
base_prompt = load_base_prompt()
final_prompt = build_json_prompt(base_prompt, tokens)

print("=" * 80)
print("PROMPT ENVIADO:")
print("=" * 80)
print(final_prompt[-500:])  # Últimos 500 caracteres
print()

# Ejecutar con cliente Gemini
client = get_gemini_client()
model_name = "gemini-1.5-pro-latest"

print("=" * 80)
print("INTENTANDO MÉTODO 1: Function/Tool Calling")
print("=" * 80)

try:
    tools = _build_tools_from_pydantic("return_corrections", CorrectionsResponse)
    print(f"Tools definidas: {json.dumps(tools, indent=2)}")

    resp = client.responses.generate(
        model=model_name,
        contents=final_prompt,
        tools=tools,
        tool_config={
            "function_calling_config": {
                "mode": "ANY",
                "allowed_function_names": ["return_corrections"],
            }
        },
    )

    print(f"\nRespuesta tipo: {type(resp)}")
    print(f"Respuesta dir: {[x for x in dir(resp) if not x.startswith('_')]}")

    # Intentar obtener texto
    text = getattr(resp, "text", None) or getattr(resp, "output_text", None)
    print(f"\nTexto de respuesta: {text}")

    # Intentar obtener function call
    called = _extract_function_call(resp, "return_corrections")
    print(f"\nFunction call extraída: {called}")

    # Ver candidatos
    if hasattr(resp, "candidates"):
        print(f"\nCandidatos: {len(resp.candidates)}")
        for i, cand in enumerate(resp.candidates):
            print(f"\n  Candidato {i}:")
            print(f"    content: {getattr(cand, 'content', None)}")
            if hasattr(cand, "content") and cand.content:
                content = cand.content
                print(f"    content.parts: {getattr(content, 'parts', None)}")
                if hasattr(content, "parts"):
                    for j, part in enumerate(content.parts):
                        print(f"      Part {j}: {part}")
                        print(f"      Part dir: {[x for x in dir(part) if not x.startswith('_')]}")

except Exception as e:
    print(f"ERROR en método 1: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
print("INTENTANDO MÉTODO 2: Structured JSON Output")
print("=" * 80)

try:
    resp2 = client.responses.generate(
        model=model_name,
        contents=final_prompt,
        response_mime_type="application/json",
        response_schema=CorrectionsResponse,
    )

    print(f"\nRespuesta tipo: {type(resp2)}")

    # Intentar parsed
    parsed = getattr(resp2, "parsed", None)
    print(f"Parsed: {parsed}")

    # Intentar texto
    text2 = getattr(resp2, "text", None) or getattr(resp2, "output_text", None)
    print(f"Texto: {text2}")

    if text2:
        try:
            data = json.loads(text2)
            print(f"JSON parseado: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error parseando JSON: {e}")

except Exception as e:
    print(f"ERROR en método 2: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)
print("Token 43 debería ser corregido:")
print("  ID: 43")
print(f"  Texto: '{tokens[43].text}'")
print(
    f"  Contexto: '...{tokens[37].text} {tokens[39].text} {tokens[41].text} {tokens[43].text}...'"
)
print("  → Debería ser 'bello' (contexto estético)")
