from __future__ import annotations

import datetime as dt
import uuid
from enum import Enum

from sqlmodel import Field, SQLModel


class Role(str, Enum):
    free = "free"
    premium = "premium"
    admin = "admin"


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: Role = Field(default=Role.free)
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())


class Project(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    owner_id: str = Field(foreign_key="user.id")
    name: str
    lang_variant: str | None = Field(default=None)  # es-ES, es-MX
    style_profile_id: str | None = Field(default=None, foreign_key="styleprofile.id")
    config_json: str | None = None
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())


class DocumentKind(str, Enum):
    docx = "docx"
    txt = "txt"
    md = "md"


class DocumentStatus(str, Enum):
    new = "new"
    queued = "queued"
    processing = "processing"
    ready = "ready"


class Document(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    name: str = Field(index=True)
    path: str | None = None
    kind: DocumentKind = Field(default=DocumentKind.docx)
    checksum: str | None = None
    status: DocumentStatus = Field(default=DocumentStatus.new)
    content_backup: str | None = None  # Stores content for demo/ephemeral storage


class RunMode(str, Enum):
    rapido = "rapido"
    profesional = "profesional"


class RunStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    exporting = "exporting"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"


class Run(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    submitted_by: str = Field(foreign_key="user.id")
    mode: RunMode = Field(default=RunMode.rapido)
    status: RunStatus = Field(default=RunStatus.queued)
    params_json: str | None = None
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())
    started_at: dt.datetime | None = None
    finished_at: dt.datetime | None = None


class RunDocumentStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RunDocument(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    run_id: str = Field(foreign_key="run.id")
    document_id: str = Field(foreign_key="document.id")
    status: RunDocumentStatus = Field(default=RunDocumentStatus.queued)
    use_ai: bool = Field(default=False)
    locked_by: str | None = None
    locked_at: dt.datetime | None = None
    heartbeat_at: dt.datetime | None = None
    attempt_count: int = Field(default=0)
    last_error: str | None = None


class ExportKind(str, Enum):
    docx = "docx"
    csv = "csv"
    jsonl = "jsonl"
    md = "md"


class Export(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    run_id: str = Field(foreign_key="run.id")
    kind: ExportKind
    path: str


class StyleProfile(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    derived_from_run_id: str | None = Field(default=None, foreign_key="run.id")
    data_json: str | None = None
    era: str | None = None
    region: str | None = None
    treatment: str | None = None
    quotes_style: str | None = None
    numeric_style: str | None = None
    leismo: bool | None = None
    solo_tilde: bool | None = None
    persona_rules: str | None = None


class Character(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    name: str
    traits_json: str | None = None


class GlossaryTerm(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    term: str
    preferred: str | None = None
    notes: str | None = None


class NormativeCatalog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    source: str
    ref: str
    title: str | None = None
    snippet: str | None = None


class SuggestionType(str, Enum):
    ortografia = "ortografia"
    puntuacion = "puntuacion"
    concordancia = "concordancia"
    estilo = "estilo"
    lexico = "lexico"
    otro = "otro"


class SuggestionSeverity(str, Enum):
    error = "error"
    warning = "warning"
    info = "info"


class SuggestionSource(str, Enum):
    rule = "rule"
    llm = "llm"


class SuggestionStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class Suggestion(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    run_id: str = Field(foreign_key="run.id", index=True)
    document_id: str = Field(foreign_key="document.id", index=True)
    token_id: int
    line: int  # 1-based paragraph/line number
    location: str | None = None  # JSON with offset info
    suggestion_type: SuggestionType = Field(default=SuggestionType.otro)
    severity: SuggestionSeverity = Field(default=SuggestionSeverity.info)
    before: str  # Original text
    after: str  # Suggested replacement
    reason: str  # Explanation
    citation_id: str | None = Field(default=None, foreign_key="normativecatalog.id")
    source: SuggestionSource = Field(default=SuggestionSource.rule)
    confidence: float | None = None  # 0.0-1.0 for LLM suggestions
    context: str | None = None  # Surrounding text
    sentence: str | None = None  # Full sentence
    status: SuggestionStatus = Field(default=SuggestionStatus.pending)
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())


class UsageLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    metric: str
    amount: int
    at: dt.datetime = Field(default_factory=lambda: dt.datetime.utcnow())
