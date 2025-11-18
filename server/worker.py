from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from pathlib import Path

from sqlmodel import select

from corrector.docx_utils import read_paragraphs, write_docx_preserving_runs, write_paragraphs
from corrector.engine import LogEntry, process_paragraphs
from corrector.model import HeuristicCorrector

from .models import (
    Document,
    Export,
    ExportKind,
    Run,
    RunDocument,
    RunDocumentStatus,
    RunStatus,
)
from .scheduler import DocumentTask
from .scheduler_registry import get_scheduler
from .storage import storage_base

logger = logging.getLogger(__name__)


class Worker:
    """Simple background worker that consumes scheduler tasks and runs the engine.

    - Uses HeuristicCorrector (cost 0) por ahora.
    - Genera exportables: corrected doc + JSONL y DOCX de informe.
    - Actualiza estados en DB.
    """

    def __init__(self, poll_interval: float = 0.5) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._poll_interval = poll_interval
        self._worker_id = str(uuid.uuid4())
        # Lease TTL (seconds) for locks; no heartbeat loop yet
        try:
            self._lock_ttl = int(os.environ.get("LOCK_TTL_SECONDS", "300"))
        except ValueError:
            self._lock_ttl = 300

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, name="worker", daemon=False)
        self._thread.start()
        logger.info("Worker started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        sched = get_scheduler()
        while not self._stop.is_set():
            task = sched.try_dispatch()
            if not task:
                time.sleep(self._poll_interval)
                continue
            try:
                # Try to lock task in DB; if cannot, skip
                if not self._try_lock_task(task):
                    continue
                self._process_task(task)
            except Exception:
                logger.exception("Error processing task")
            finally:
                try:
                    sched.finish(task)
                except Exception:
                    logger.warning("Error finishing task", exc_info=True)

    def _process_task(self, task: DocumentTask) -> None:
        from .db import session_scope

        # Extraer datos necesarios dentro de la sesión
        with session_scope() as session:
            doc = session.get(Document, task.document_id)
            run_doc = session.exec(
                select(RunDocument).where(
                    RunDocument.run_id == task.run_id, RunDocument.document_id == task.document_id
                )
            ).first()
            run = session.get(Run, task.run_id)
            if not doc or not run_doc or not run:
                logger.warning("Task references missing entities: %s", task)
                return

            # Extraer valores antes de salir de la sesión
            doc_path = doc.path
            doc_name = doc.name
            use_ai = run_doc.use_ai if hasattr(run_doc, "use_ai") else False

            # status/lock were set in _try_lock_task
            session.add(run_doc)
            session.commit()

        # Paths de entrada/salida
        if not doc_path:
            self._mark_failed(task, reason="missing document path")
            return
        input_path = Path(doc_path)

        # Auto-recreate file from DB backup if missing (ephemeral storage)
        if not input_path.exists():
            logger.warning(f"Document file missing: {doc_path}, checking DB backup...")
            with session_scope() as sess:
                doc_rec = sess.get(Document, task.document_id)
                if doc_rec and doc_rec.content_backup:
                    logger.info(f"Recreating document from DB backup: {doc_name}")
                    input_path.parent.mkdir(parents=True, exist_ok=True)
                    content_lines = doc_rec.content_backup.split("\n")
                    write_paragraphs(content_lines, str(input_path))
                    logger.info(f"✅ File recreated successfully: {input_path}")
                else:
                    self._mark_failed(task, reason="document not found and no backup available")
                    return

        out_base = storage_base() / task.user_id / task.project_id / "runs" / task.run_id
        out_base.mkdir(parents=True, exist_ok=True)
        # Usar el nombre original del documento (sin el prefijo de checksum) para los outputs
        stem = Path(doc_name).stem
        # Salidas
        corrected_ext = ".docx" if input_path.suffix.lower() == ".docx" else ".txt"
        corrected_path = out_base / f"{stem}.corrected{corrected_ext}"
        log_jsonl_path = out_base / f"{stem}.corrections.jsonl"
        log_docx_path = out_base / f"{stem}.corrections.docx"
        changelog_csv_path = out_base / f"{stem}.changelog.csv"
        summary_md_path = out_base / f"{stem}.summary.md"

        # Seleccionar corrector según configuración
        if use_ai:
            from corrector.llm import LLMNotConfigured
            from corrector.model import GeminiCorrector

            try:
                corrector = GeminiCorrector()
                logger.info("✅ Using Gemini AI corrector for document: %s", doc_name)
            except LLMNotConfigured:
                logger.warning("⚠️  Gemini not configured, falling back to HeuristicCorrector")
                corrector = HeuristicCorrector()
        else:
            corrector = HeuristicCorrector()
            logger.info("📝 Using HeuristicCorrector (no AI) for document: %s", doc_name)

        try:
            logger.info("📄 Processing document: %s", doc_name)
            logger.info("   Input: %s", input_path)
            logger.info("   Output: %s", corrected_path)

            # Process using process_paragraphs to get LogEntry objects
            paragraphs = read_paragraphs(str(input_path))
            corrected_paragraphs, log_entries = process_paragraphs(
                paragraphs, corrector, chunk_words=0, overlap_words=0
            )

            # Save corrected document
            if input_path.suffix.lower() == ".docx":
                write_docx_preserving_runs(
                    str(input_path), corrected_paragraphs, str(corrected_path)
                )
            else:
                write_paragraphs(corrected_paragraphs, str(corrected_path))

            # Persist suggestions to database
            logger.info("💾 Saving %d suggestions to database...", len(log_entries))
            self._persist_suggestions(task, log_entries)

            # Write JSONL log for compatibility
            self._write_log_jsonl(log_jsonl_path, log_entries)

            # Write DOCX log
            self._write_log_docx(log_docx_path, log_entries, source_filename=doc_name)

            logger.info("✅ Document processing completed: %s", doc_name)
            logger.info("📊 Building CSV changelog...")
            # Construir CSV a partir del JSONL
            self._build_csv_from_jsonl(log_jsonl_path, changelog_csv_path)

            logger.info("📝 Building summary/editorial letter...")
            # Construir carta editorial (resumen)
            self._build_summary_md(summary_md_path, docname=stem, jsonl_path=log_jsonl_path)

            logger.info("💾 Saving exports to database...")
            # Guardar exports
            try:
                with session_scope() as session:
                    session.add_all(
                        [
                            Export(
                                run_id=task.run_id, kind=ExportKind.docx, path=str(corrected_path)
                            ),
                            Export(
                                run_id=task.run_id, kind=ExportKind.jsonl, path=str(log_jsonl_path)
                            ),
                            Export(
                                run_id=task.run_id, kind=ExportKind.docx, path=str(log_docx_path)
                            ),
                            Export(
                                run_id=task.run_id,
                                kind=ExportKind.csv,
                                path=str(changelog_csv_path),
                            ),
                            Export(
                                run_id=task.run_id, kind=ExportKind.md, path=str(summary_md_path)
                            ),
                        ]
                    )
                    rd = session.exec(
                        select(RunDocument).where(
                            RunDocument.run_id == task.run_id,
                            RunDocument.document_id == task.document_id,
                        )
                    ).first()
                    if rd:
                        rd.status = RunDocumentStatus.completed
                        session.add(rd)
                    # Update run status if all docs done
                    rdocs = session.exec(
                        select(RunDocument).where(RunDocument.run_id == task.run_id)
                    ).all()
                    if rdocs and all(r.status == RunDocumentStatus.completed for r in rdocs):
                        r = session.get(Run, task.run_id)
                        if r:
                            r.status = RunStatus.completed
                            session.add(r)
                logger.info("✅ Exports saved successfully")
            except Exception as db_error:
                logger.exception("❌ Database error while saving exports: %s", db_error)
                self._mark_failed(task, reason=f"database error: {str(db_error)}")
                raise
        except Exception as e:
            logger.exception("❌ Processing error: %s", e)
            self._mark_failed(task, reason=f"engine error: {str(e)}")

    def _mark_failed(self, task: DocumentTask, reason: str) -> None:
        from .db import session_scope

        with session_scope() as session:
            rd = session.exec(
                select(RunDocument).where(
                    RunDocument.run_id == task.run_id, RunDocument.document_id == task.document_id
                )
            ).first()
            if rd:
                rd.status = RunDocumentStatus.failed
                rd.last_error = reason
                rd.locked_by = None
                rd.locked_at = None
                session.add(rd)
            r = session.get(Run, task.run_id)
            if r:
                r.status = RunStatus.failed
                session.add(r)
        logger.error("Task failed: %s (%s)", task, reason)

    def _try_lock_task(self, task: DocumentTask) -> bool:
        """Attempt to acquire a DB lock (lease) for the RunDocument before processing.

        Returns True if lock acquired; False otherwise.
        """
        import datetime as dt

        from .db import session_scope

        now = dt.datetime.utcnow()
        lease_deadline = now - dt.timedelta(seconds=self._lock_ttl)

        with session_scope() as session:
            rd = session.exec(
                select(RunDocument).where(
                    RunDocument.run_id == task.run_id, RunDocument.document_id == task.document_id
                )
            ).first()
            if not rd:
                return False
            # If locked and not expired, someone else is working on it
            if rd.locked_by and rd.locked_at and rd.locked_at > lease_deadline:
                return False
            # Acquire lock
            rd.locked_by = self._worker_id
            rd.locked_at = now
            rd.status = RunDocumentStatus.processing
            rd.attempt_count = (rd.attempt_count or 0) + 1
            session.add(rd)
            return True

    def _build_csv_from_jsonl(self, jsonl_path: Path, csv_path: Path) -> None:
        import csv
        import json

        with csv_path.open("w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out)
            header = [
                "token_id",
                "line",
                "original",
                "corrected",
                "reason",
                "context",
                "chunk_index",
                "sentence",
            ]
            writer.writerow(header)
            try:
                with open(jsonl_path, encoding="utf-8") as f_in:
                    for line in f_in:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        row = [
                            obj.get("token_id", ""),
                            obj.get("line", ""),
                            obj.get("original", ""),
                            obj.get("corrected", ""),
                            obj.get("reason", ""),
                            obj.get("context", ""),
                            obj.get("chunk_index", ""),
                            obj.get("sentence", ""),
                        ]
                        writer.writerow(row)
            except FileNotFoundError:
                pass

    def _persist_suggestions(self, task: DocumentTask, log_entries: list[LogEntry]) -> None:
        """Persist log entries as Suggestion records in database."""
        from .db import session_scope
        from .models import Suggestion, SuggestionSeverity, SuggestionSource, SuggestionType

        with session_scope() as session:
            for entry in log_entries:
                # Classify suggestion type based on reason keywords
                reason_lower = entry.reason.lower()
                suggestion_type = SuggestionType.otro
                if any(kw in reason_lower for kw in ["ortografía", "ortografia", "spelling"]):
                    suggestion_type = SuggestionType.ortografia
                elif any(kw in reason_lower for kw in ["puntuación", "puntuacion", "punctuation"]):
                    suggestion_type = SuggestionType.puntuacion
                elif any(kw in reason_lower for kw in ["concordancia", "agreement"]):
                    suggestion_type = SuggestionType.concordancia
                elif any(kw in reason_lower for kw in ["estilo", "style"]):
                    suggestion_type = SuggestionType.estilo
                elif any(
                    kw in reason_lower
                    for kw in ["léxico", "lexico", "lexical", "confusión", "confusion"]
                ):
                    suggestion_type = SuggestionType.lexico

                # Default severity
                severity = SuggestionSeverity.info
                if "[ELIMINACIÓN]" in entry.reason:
                    severity = SuggestionSeverity.warning

                # Determine source (rule vs llm)
                source = SuggestionSource.llm if task.use_ai else SuggestionSource.rule

                suggestion = Suggestion(
                    run_id=task.run_id,
                    document_id=task.document_id,
                    token_id=entry.token_id,
                    line=entry.line,
                    suggestion_type=suggestion_type,
                    severity=severity,
                    before=entry.original,
                    after=entry.corrected,
                    reason=entry.reason,
                    source=source,
                    context=entry.context,
                    sentence=entry.sentence,
                )
                session.add(suggestion)
            session.commit()

    def _write_log_jsonl(self, path: Path, entries: list[LogEntry]) -> None:
        """Write log entries to JSONL file."""
        import json

        with path.open("w", encoding="utf-8") as f:
            for e in entries:
                f.write(
                    json.dumps(
                        {
                            "token_id": e.token_id,
                            "line": e.line,
                            "original": e.original,
                            "corrected": e.corrected,
                            "reason": e.reason,
                            "context": e.context,
                            "chunk_index": e.chunk_index,
                            "sentence": e.sentence,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    def _write_log_docx(
        self, path: Path, entries: list[LogEntry], source_filename: str | None = None
    ) -> None:
        """Write log entries to formatted DOCX file."""
        # Import the existing function from engine
        from corrector.engine import _write_log_docx as engine_write_log_docx

        engine_write_log_docx(str(path), entries, source_filename=source_filename)

    def _build_summary_md(self, summary_path: Path, *, docname: str, jsonl_path: Path) -> None:
        import json
        from collections import Counter

        total = 0
        reasons: Counter[str] = Counter()
        try:
            with open(jsonl_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    total += 1
                    reasons[obj.get("reason", "")] += 1
        except FileNotFoundError:
            pass

        top_reasons = reasons.most_common(10)
        lines: list[str] = []
        lines.append(f"# Carta de edición — {docname}")
        lines.append("")
        lines.append(f"Total de correcciones: {total}")
        if top_reasons:
            lines.append("")
            lines.append("## Principales motivos")
            for r, c in top_reasons:
                if not r:
                    r = "(sin motivo)"
                lines.append(f"- {r}: {c}")
        lines.append("")
        lines.append("## Observaciones")
        lines.append("- Este resumen se genera automáticamente a partir del log de correcciones.")
        lines.append("- Revise las decisiones finales en el documento con control de cambios.")
        lines.append("")
        lines.append("## Próximos pasos sugeridos")
        lines.append("- Acepte/rechace cambios en DOCX según criterio editorial.")
        lines.append("- Revise consistencias intercapítulos y glosario del proyecto.")
        lines.append("- Considere activar el modo Profesional para logs detallados y reglas finas.")

        summary_path.write_text("\n".join(lines), encoding="utf-8")
