
import re
from pathlib import Path

from corrector.engine import process_document
from corrector.model import GeminiCorrector


class _FC:
    def __init__(self, name, args):
        self.name = name
        self.args = args


class _Part:
    def __init__(self, function_call=None):
        self.function_call = function_call


class _Content:
    def __init__(self, parts):
        self.parts = parts


class _Candidate:
    def __init__(self, content):
        self.content = content


class _Resp:
    def __init__(self, candidates):
        self.candidates = candidates


class _ResponsesAPI:
    def generate(self, model, contents, **kwargs):
        prompt = contents
        # find token ids for target words in the prompt rendering
        m_baca = re.search(r"(\d+):W:baca\b", prompt)
        m_ojear = re.search(r"(\d+):W:ojear\b", prompt)
        corrections = []
        if m_baca:
            corrections.append({
                "token_id": int(m_baca.group(1)),
                "replacement": "vaca",
                "reason": "Confusión baca/vaca (techo del coche)",
                "original": "baca",
            })
        if m_ojear:
            corrections.append({
                "token_id": int(m_ojear.group(1)),
                "replacement": "hojear",
                "reason": "Confusión ojear/hojear (pasar páginas)",
                "original": "ojear",
            })
        fc = _FC("return_corrections", {"corrections": corrections})
        return _Resp([_Candidate(_Content([_Part(function_call=fc)]))])


class _FakeClient:
    def __init__(self):
        self.responses = _ResponsesAPI()


def test_gemini_corrector_with_tools_preserves_proper_names(monkeypatch, tmp_path: Path):
    # Monkeypatch client factory to use fake responses API
    import corrector.model as model_mod

    monkeypatch.setattr(model_mod, "get_gemini_client", lambda: _FakeClient())

    input_doc = tmp_path / "entrada.docx"
    paragraphs = [
        "María viajó a Barcelona. La baca del coche estaba sucia.",
        "Luego decidió ojear el libro rápidamente.",
    ]

    # write minimal docx via fallback
    from corrector.docx_utils import read_paragraphs, write_paragraphs
    write_paragraphs(paragraphs, str(input_doc))

    out_doc = tmp_path / "salida.docx"
    log_json = tmp_path / "log.jsonl"

    corr = GeminiCorrector(base_prompt_text="")
    process_document(str(input_doc), str(out_doc), str(log_json), corr, chunk_words=0, overlap_words=0)

    # Verify corrections applied and proper names preserved
    out_paras = read_paragraphs(str(out_doc))
    full = "\n".join(out_paras)
    assert "La vaca del coche" in full
    assert "María" in full
    assert "Barcelona" in full
