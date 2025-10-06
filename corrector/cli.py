from __future__ import annotations

import argparse
from pathlib import Path

from .engine import process_document
from .model import GeminiCorrector, HeuristicCorrector
from .prompt import load_base_prompt, build_json_prompt
from .docx_utils import read_paragraphs
from .text_utils import tokenize, count_word_tokens

try:
    from settings import get_settings
    settings = get_settings()
except ImportError:
    settings = None


def main() -> None:
    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    parser = argparse.ArgumentParser(description="Corrector ortográfico/contextual en español (DOCX)")
    parser.add_argument("input", help="Ruta del documento DOCX de entrada")
    parser.add_argument("--out", dest="out", help="Ruta de salida DOCX", default=None)
    parser.add_argument("--log", dest="log", help="Ruta del log JSONL", default=None)
    parser.add_argument("--chunk-words", dest="chunk_words", type=int, default=8000, help="Máximo de palabras por chunk (0 = todo)")
    parser.add_argument("--overlap-words", dest="overlap_words", type=int, default=800, help="Solape de palabras entre chunks")
    default_model = settings.gemini_model if settings and settings.gemini_model else "gemini-2.5-flash"
    parser.add_argument("--model", dest="model_name", default=default_model, help="Modelo Gemini a usar")
    parser.add_argument("--auto-chunk", action="store_true", help="Dimensionado automático del chunk según ventana de contexto")
    parser.set_defaults(auto_chunk=True)
    parser.add_argument("--base-prompt", dest="base_prompt_path", default=None, help="Ruta de base-prompt.md si no está en raíz")
    parser.add_argument("--local-heuristics", action="store_true", help="Usar corrector local heurístico (sin API)")
    parser.add_argument("--no-preserve-format", action="store_true", help="No preservar formato DOCX (escritura simple de párrafos)")
    parser.add_argument("--log-docx", dest="log_docx", default=None, help="Ruta del reporte DOCX del log (por defecto input.corrections.docx)")
    parser.add_argument("--no-log-docx", action="store_true", help="No generar el reporte DOCX del log")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"No existe el archivo: {in_path}")

    # Si no se especifica salida, usar directorio outputs/
    if args.out:
        out_path = Path(args.out)
    else:
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        out_path = outputs_dir / f"{in_path.stem}.corrected.docx"

    if args.log:
        log_path = Path(args.log)
    else:
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        log_path = outputs_dir / f"{in_path.stem}.corrections.jsonl"

    if args.log_docx:
        log_docx_path = Path(args.log_docx)
    else:
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        log_docx_path = outputs_dir / f"{in_path.stem}.corrections.docx"

    base_prompt = load_base_prompt(args.base_prompt_path)
    if args.local_heuristics:
        corrector = HeuristicCorrector()
    else:
        corrector = GeminiCorrector(model_name=args.model_name, base_prompt_text=base_prompt)

    # Auto-dimensionado de chunk si se solicita
    chunk_words = args.chunk_words
    overlap_words = args.overlap_words
    if args.auto_chunk:
        paragraphs_for_est = read_paragraphs(str(in_path))
        full_text = "\n".join(paragraphs_for_est)
        tokens = tokenize(full_text)
        if tokens:
            # Muestra de hasta 2000 tokens para estimación
            sample_tokens = tokens[: min(2000, len(tokens))]
            base_chars = len(build_json_prompt(base_prompt, []))
            sample_chars = len(build_json_prompt(base_prompt, sample_tokens))
            # Estimar tokens LLM ~ chars/4
            base_llm_tokens = max(base_chars // 4, 1)
            sample_llm_tokens = max((sample_chars - base_chars) // 4, 1)
            word_count = max(count_word_tokens(sample_tokens), 1)
            tokens_per_word = max(sample_llm_tokens / word_count, 2.0)
            # Ventana por modelo (simple): 128k para Gemini 1.5*
            model_ctx = 128_000
            if "1.5" not in args.model_name:
                model_ctx = 128_000
            target_ratio = 0.15  # Reducido de 0.7 a 0.15 para chunks más pequeños
            output_reserve = 2000
            margin = 500
            input_budget = int(model_ctx * target_ratio) - output_reserve - margin - base_llm_tokens
            est_chunk_words = int(max(input_budget / tokens_per_word, 300))
            # Límites razonables - reducidos para mejor progreso visible
            est_chunk_words = max(300, min(est_chunk_words, 1000))
            chunk_words = est_chunk_words
            overlap_words = max(int(chunk_words * 0.10), 200)

    process_document(
        str(in_path),
        str(out_path),
        str(log_path),
        corrector,
        chunk_words=chunk_words,
        overlap_words=overlap_words,
        preserve_format=not args.no_preserve_format,
        log_docx_path=(str(log_docx_path) if not args.no_log_docx else None),
        enable_docx_log=(not args.no_log_docx),
    )


if __name__ == "__main__":
    main()
