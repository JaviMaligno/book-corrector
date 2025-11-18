"""API endpoints for managing correction suggestions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .db import get_session
from .deps import get_current_user
from .models import Run, Suggestion, SuggestionStatus, User
from .schemas import (
    BulkUpdateSuggestionsRequest,
    SuggestionResponse,
    SuggestionsListResponse,
    UpdateSuggestionStatusRequest,
)

router = APIRouter(prefix="/suggestions", tags=["suggestions"])


def _suggestion_to_response(suggestion: Suggestion) -> SuggestionResponse:
    """Convert Suggestion model to API response."""
    return SuggestionResponse(
        id=suggestion.id,
        run_id=suggestion.run_id,
        document_id=suggestion.document_id,
        token_id=suggestion.token_id,
        line=suggestion.line,
        suggestion_type=suggestion.suggestion_type.value,
        severity=suggestion.severity.value,
        before=suggestion.before,
        after=suggestion.after,
        reason=suggestion.reason,
        source=suggestion.source.value,
        confidence=suggestion.confidence,
        context=suggestion.context,
        sentence=suggestion.sentence,
        status=suggestion.status.value,
    )


@router.get("/runs/{run_id}/suggestions", response_model=SuggestionsListResponse)
def list_suggestions(
    run_id: str,
    status: str | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all suggestions for a run, optionally filtered by status."""
    # Verify run exists and user owns it
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Build query
    query = select(Suggestion).where(Suggestion.run_id == run_id)
    if status:
        try:
            status_enum = SuggestionStatus(status)
            query = query.where(Suggestion.status == status_enum)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}") from err

    suggestions = session.exec(query).all()

    return SuggestionsListResponse(
        run_id=run_id,
        total=len(suggestions),
        suggestions=[_suggestion_to_response(s) for s in suggestions],
    )


@router.get("/suggestions/{suggestion_id}", response_model=SuggestionResponse)
def get_suggestion(
    suggestion_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a single suggestion by ID."""
    suggestion = session.get(Suggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    # Verify user owns the run
    run = session.get(Run, suggestion.run_id)
    if not run or run.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return _suggestion_to_response(suggestion)


@router.patch("/suggestions/{suggestion_id}", response_model=SuggestionResponse)
def update_suggestion_status(
    suggestion_id: str,
    request: UpdateSuggestionStatusRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update the status of a single suggestion (accept/reject)."""
    suggestion = session.get(Suggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    # Verify user owns the run
    run = session.get(Run, suggestion.run_id)
    if not run or run.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update status
    suggestion.status = SuggestionStatus(request.status)
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)

    return _suggestion_to_response(suggestion)


@router.post("/runs/{run_id}/suggestions/bulk-update")
def bulk_update_suggestions(
    run_id: str,
    request: BulkUpdateSuggestionsRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Bulk update status of multiple suggestions."""
    # Verify run exists and user owns it
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update all suggestions
    updated_count = 0
    for suggestion_id in request.suggestion_ids:
        suggestion = session.get(Suggestion, suggestion_id)
        if suggestion and suggestion.run_id == run_id:
            suggestion.status = SuggestionStatus(request.status)
            session.add(suggestion)
            updated_count += 1

    session.commit()

    return {"updated": updated_count, "total_requested": len(request.suggestion_ids)}


@router.post("/runs/{run_id}/suggestions/accept-all")
def accept_all_suggestions(
    run_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Accept all pending suggestions for a run."""
    # Verify run exists and user owns it
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update all pending suggestions to accepted
    suggestions = session.exec(
        select(Suggestion).where(
            Suggestion.run_id == run_id, Suggestion.status == SuggestionStatus.pending
        )
    ).all()

    for suggestion in suggestions:
        suggestion.status = SuggestionStatus.accepted
        session.add(suggestion)

    session.commit()

    return {"accepted": len(suggestions)}


@router.post("/runs/{run_id}/suggestions/reject-all")
def reject_all_suggestions(
    run_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Reject all pending suggestions for a run."""
    # Verify run exists and user owns it
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update all pending suggestions to rejected
    suggestions = session.exec(
        select(Suggestion).where(
            Suggestion.run_id == run_id, Suggestion.status == SuggestionStatus.pending
        )
    ).all()

    for suggestion in suggestions:
        suggestion.status = SuggestionStatus.rejected
        session.add(suggestion)

    session.commit()

    return {"rejected": len(suggestions)}


@router.post("/runs/{run_id}/export-with-accepted")
def export_document_with_accepted_corrections(
    run_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Generate final document with only accepted corrections applied."""
    from pathlib import Path

    from fastapi.responses import Response

    from corrector.docx_utils import read_paragraphs
    from corrector.text_utils import (
        Correction,
        apply_token_corrections,
        detokenize,
        tokenize,
    )
    from server.models import Document, RunDocument
    from server.storage import storage_base

    # Verify run exists and user owns it
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get accepted suggestions, sorted by token_id
    accepted = session.exec(
        select(Suggestion)
        .where(Suggestion.run_id == run_id, Suggestion.status == SuggestionStatus.accepted)
        .order_by(Suggestion.token_id)
    ).all()

    if not accepted:
        raise HTTPException(status_code=400, detail="No accepted corrections found")

    # Get the first document for this run (for now, assume single document)
    run_doc = session.exec(select(RunDocument).where(RunDocument.run_id == run_id)).first()
    if not run_doc:
        raise HTTPException(status_code=404, detail="No document found for this run")

    doc = session.get(Document, run_doc.document_id)
    if not doc or not doc.path:
        raise HTTPException(status_code=404, detail="Document not found")

    # Read original document
    input_path = Path(doc.path)
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Source document file not found")

    # Process document with accepted corrections only
    paragraphs = read_paragraphs(str(input_path))
    full_text = "\n".join(paragraphs)
    tokens = tokenize(full_text)

    # Convert Suggestion records to correction specs
    corrections = []
    for sugg in accepted:
        corrections.append(
            Correction(
                token_id=sugg.token_id,
                replacement=sugg.after,
                reason=sugg.reason,
                original=sugg.before,
            )
        )

    # Apply corrections
    corrected_tokens = apply_token_corrections(tokens, corrections)
    corrected_text = detokenize(corrected_tokens)
    corrected_paragraphs = corrected_text.split("\n")

    # Generate output file
    out_base = storage_base() / current_user.id / run.project_id / "runs" / run_id
    out_base.mkdir(parents=True, exist_ok=True)

    stem = Path(doc.name).stem
    output_path = out_base / f"{stem}.accepted.docx"

    # Save corrected document (create new document for clarity)
    from corrector.docx_utils import write_paragraphs

    write_paragraphs(corrected_paragraphs, str(output_path))

    # Read the file and return as Response (better CORS support than FileResponse)
    with open(output_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{stem}.accepted.docx"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
