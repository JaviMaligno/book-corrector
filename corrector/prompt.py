from __future__ import annotations

from pathlib import Path
from typing import List

from .text_utils import Token


def load_base_prompt(path: str | None = None) -> str:
    if path is None:
        p = Path("base-prompt.md")
    else:
        p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8")
    # Fallback default
    return (
        "Actúa como corrector profesional en español. Corrige ortografía, puntuación, gramática y usos confusos."
    )


def build_json_prompt(base_prompt: str, tokens: List[Token]) -> str:
    """Build a compact instruction asking for precise token-level corrections.

    The model must only return JSON with structure:
    {"corrections": [{"token_id": int, "replacement": str, "reason": str, "original": str?}]}
    """
    # Render tokens with ids for deterministic referencing
    rendered_tokens = []
    for t in tokens:
        if t.kind in ("word", "number"):
            kind = "W"
        elif t.kind == "punct":
            kind = "P"
        elif t.kind == "newline":
            kind = "N"
        else:
            kind = "S"  # space/other
        # Escape newlines in preview
        text_preview = t.text.replace("\n", "\\n")
        rendered_tokens.append(f"{t.id}:{kind}:{text_preview}")

    schema = (
        "Si dispones de herramientas, llama a 'return_corrections' con la lista de correcciones. "
        "En ausencia de herramientas, responde SOLO con JSON válido UTF-8 sin texto adicional. "
        "Esquema: {\"corrections\": [{\"token_id\": int, \"replacement\": str, \"reason\": str, \"original\"?: str}]}\n"
        "- token_id apunta al índice exacto del token a corregir.\n"
        "- Solo corrige tokens de tipo palabra/número si es necesario (no reescribas todo).\n"
        "- Mantén mayúsculas adecuadas y acentos.\n"
        "- Considera parejas confusas por contexto: bello/vello, vaca/baca, hojear/ojear, vaya/valla/baya, etc.\n"
    )

    model_instruction = (
        f"{base_prompt}\n\n"
        f"Tu tarea: identifica SOLO las palabras que deben corregirse y devuelve JSON con la corrección.\n"
        f"Tokens etiquetados (id:tipo:texto_escapado):\n"
        f"{' '.join(rendered_tokens)}\n\n"
        f"{schema}"
    )
    return model_instruction
