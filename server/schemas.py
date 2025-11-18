from __future__ import annotations

from pydantic import BaseModel, Field


class MeLimits(BaseModel):
    plan: str
    max_runs_concurrent: int
    max_docs_per_run: int
    max_docs_concurrent: int
    rate_limit_rpm: int
    ai_enabled: bool


class CreateRunRequest(BaseModel):
    project_id: str
    documents: list[str] = Field(default_factory=list)
    mode: str = Field(default="rapido", pattern="^(rapido|profesional)$")
    use_ai: bool = True


class CreateRunResponse(BaseModel):
    run_id: str
    accepted_documents: list[str]
    queued: int


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    processed_documents: int = 0
    total_documents: int = 0


class SuggestionResponse(BaseModel):
    id: str
    run_id: str
    document_id: str
    token_id: int
    line: int
    suggestion_type: str
    severity: str
    before: str
    after: str
    reason: str
    source: str
    confidence: float | None = None
    context: str | None = None
    sentence: str | None = None
    status: str


class SuggestionsListResponse(BaseModel):
    run_id: str
    total: int
    suggestions: list[SuggestionResponse]


class UpdateSuggestionStatusRequest(BaseModel):
    status: str = Field(pattern="^(pending|accepted|rejected)$")


class BulkUpdateSuggestionsRequest(BaseModel):
    suggestion_ids: list[str]
    status: str = Field(pattern="^(accepted|rejected)$")


class ExportWithCorrectionsRequest(BaseModel):
    run_id: str
    only_accepted: bool = True  # If True, only apply accepted corrections
