from __future__ import annotations

import json
from typing import List, Protocol, Any, Dict

from pydantic import BaseModel

from .llm import get_gemini_client, LLMNotConfigured
from .text_utils import Token
from .prompt import build_json_prompt


class CorrectionSpec(BaseModel):
    token_id: int
    replacement: str
    reason: str
    original: str | None = None


class BaseCorrector(Protocol):
    def correct_tokens(self, tokens: List[Token]) -> List[CorrectionSpec]:
        ...


class CorrectionsResponse(BaseModel):
    corrections: List[CorrectionSpec] = []


class GeminiCorrector:
    def __init__(self, model_name: str = "gemini-2.5-flash", base_prompt_text: str | None = None) -> None:
        self.model_name = model_name
        self.base_prompt_text = base_prompt_text or ""
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            self._client = get_gemini_client()

    def correct_tokens(self, tokens: List[Token]) -> List[CorrectionSpec]:
        self._ensure_client()
        prompt = build_json_prompt(self.base_prompt_text, tokens)
        try:
            # Use models.generate_content with JSON output
            resp = self._client.models.generate_content(
                model=self.model_name,
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                config={"response_mime_type": "application/json"},
            )

            # Extract text from response
            text = getattr(resp, "text", None)
            if not text:
                # Try alternative attributes
                if hasattr(resp, 'candidates') and resp.candidates:
                    cand = resp.candidates[0]
                    if hasattr(cand, 'content') and cand.content:
                        if hasattr(cand.content, 'parts') and cand.content.parts:
                            part = cand.content.parts[0]
                            text = getattr(part, 'text', None)

            if text:
                data = json.loads(text)
                items = data.get("corrections") if isinstance(data, dict) else data
                if isinstance(items, list):
                    return [CorrectionSpec(**it) for it in items]
            return []
        except LLMNotConfigured:
            raise
        except Exception as e:
            # Log the error for debugging but don't crash
            import logging
            logging.getLogger(__name__).warning(f"Error in correct_tokens: {e}", exc_info=True)
            return []


class HeuristicCorrector:
    """Simple local heuristic corrector used for testing/demo.

    - corrige "baca"->"vaca" si contexto contiene coche/carro/auto
    - corrige "vello"->"bello" cuando aparezca con adjetivos estéticos
    - corrige "ojear"->"hojear" si contexto contiene libro/revista
    """

    def correct_tokens(self, tokens: List[Token]) -> List[CorrectionSpec]:
        text_lower = [t.text.lower() for t in tokens]
        results: List[CorrectionSpec] = []
        for i, t in enumerate(tokens):
            if t.kind != "word":
                continue
            w = t.text.lower()
            # baca/vaca
            if w == "baca":
                window = " ".join(text_lower[max(0, i - 5) : i + 6])
                if any(k in window for k in ["coche", "carro", "auto", "vehículo", "vehiculo"]):
                    results.append(
                        CorrectionSpec(token_id=i, replacement=_preserve_case(t.text, "vaca"), reason="Confusión baca/vaca (techo del coche)", original=t.text)
                    )
            # vello/bello
            if w == "vello":
                window = " ".join(text_lower[max(0, i - 5) : i + 6])
                if any(k in window for k in ["hermoso", "bonito", "precioso", "arte"]):
                    results.append(
                        CorrectionSpec(token_id=i, replacement=_preserve_case(t.text, "bello"), reason="Confusión vello/bello (estético)", original=t.text)
                    )
            # ojear/hojear
            if w == "ojear":
                window = " ".join(text_lower[max(0, i - 5) : i + 6])
                if any(k in window for k in ["libro", "revista", "páginas", "paginas"]):
                    results.append(
                        CorrectionSpec(token_id=i, replacement=_preserve_case(t.text, "hojear"), reason="Confusión ojear/hojear (pasar páginas)", original=t.text)
                    )
        return results


def _preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement.capitalize()
    return replacement


def _build_tools_from_pydantic(function_name: str, model: type[BaseModel]) -> list[dict[str, Any]]:
    """Build Gemini 'tools' function_declarations from a Pydantic model schema."""
    schema: Dict[str, Any] = model.model_json_schema()
    # Ensure top-level is an object; Gemini expects JSON Schema draft
    if schema.get("type") != "object":
        schema = {"type": "object", "properties": {"value": schema}, "required": ["value"]}
    return [
        {
            "function_declarations": [
                {
                    "name": function_name,
                    "parameters": schema,
                }
            ]
        }
    ]


def _extract_function_call(resp: Any, name: str) -> Dict[str, Any] | None:
    """Extract function call arguments from a Gemini Responses object."""
    try:
        cands = getattr(resp, "candidates", None)
        if not cands:
            return None
        for c in cands:
            content = getattr(c, "content", None)
            if not content:
                continue
            parts = getattr(content, "parts", None)
            if not parts:
                continue
            for p in parts:
                fc = getattr(p, "function_call", None) or getattr(p, "functionCall", None)
                if not fc:
                    continue
                fname = getattr(fc, "name", None) or (isinstance(fc, dict) and fc.get("name"))
                if fname != name:
                    continue
                args = getattr(fc, "args", None) or (isinstance(fc, dict) and fc.get("args"))
                if isinstance(args, dict):
                    return args
    except Exception:
        return None
    return None
