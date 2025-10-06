from pathlib import Path

from corrector.docx_utils import read_paragraphs, write_paragraphs
from corrector.engine import process_document
from corrector.model import HeuristicCorrector


def test_process_document_with_heuristic_corrector(tmp_path: Path):
    # Create input DOCX
    input_doc = tmp_path / "entrada.docx"
    paragraphs = [
        "La baca del coche estaba sucia.",
        "Luego decidió ojear el libro rápidamente.",
    ]
    write_paragraphs(paragraphs, str(input_doc))

    # Run engine
    output_doc = tmp_path / "salida.docx"
    log_path = tmp_path / "log.jsonl"

    corrector = HeuristicCorrector()
    process_document(
        str(input_doc), str(output_doc), str(log_path), corrector, chunk_words=10, overlap_words=3
    )

    # Validate output docx content
    out_paragraphs = read_paragraphs(str(output_doc))
    full_text = "\n".join(out_paragraphs)
    assert "La vaca del coche" in full_text
    assert "hojear el libro" in full_text

    # Validate log
    log_lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) >= 2
    # Quick shape check: JSON lines contain keys we expect
    assert "\"original\"" in log_lines[0]
    assert "\"corrected\"" in log_lines[0]

