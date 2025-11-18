import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from corrector.docx_utils import read_paragraphs
from corrector.engine import process_document
from corrector.model import GeminiCorrector
from corrector.prompt import load_base_prompt

# Load .env file
load_dotenv()

RUN_LIVE = os.getenv("RUN_GEMINI_INTEGRATION") == "1"
API_SET = bool(os.getenv("GOOGLE_API_KEY"))

pytestmark = pytest.mark.skipif(
    not (RUN_LIVE and API_SET), reason="Set RUN_GEMINI_INTEGRATION=1 and GOOGLE_API_KEY to run"
)


def test_gemini_live_corrections_and_proper_names(tmp_path: Path):
    # Usar el archivo de ejemplo incluido en el repo
    sample = Path(__file__).resolve().parent / "samples" / "gemini_live_input.docx"
    input_doc = sample

    out_doc = tmp_path / "salida.docx"
    log_json = tmp_path / "log.jsonl"

    base_prompt = load_base_prompt()
    corrector = GeminiCorrector(base_prompt_text=base_prompt)

    process_document(
        str(input_doc),
        str(out_doc),
        str(log_json),
        corrector,
        chunk_words=0,
        overlap_words=0,
        preserve_format=True,
        enable_docx_log=False,
    )

    # Read outputs
    out_paragraphs = read_paragraphs(str(out_doc))
    out_text = "\n".join(out_paragraphs)
    assert "María" in out_text
    assert "Barcelona" in out_text

    lines = [ln for ln in log_json.read_text(encoding="utf-8").splitlines() if ln.strip()]
    entries = [json.loads(ln) for ln in lines]
    # Correcciones pueden ser cero dependiendo del modelo/prompts; si hay, validar que sean relevantes
    originals = {e.get("original", "").lower() for e in entries}
    # Si hay alguna, preferimos que toque una confusión típica
    if originals:
        assert any(w in originals for w in {"baca", "ojear", "vello"})

    # Proper names should not be targets of correction
    assert "maría" not in originals
    assert "barcelona" not in originals
