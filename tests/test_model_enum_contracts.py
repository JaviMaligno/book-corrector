"""Preserve wire, diagnostic and SQL enum contracts during Python modernization."""

import json
import socket

import pytest
from pydantic import TypeAdapter
from sqlalchemy.dialects.sqlite import dialect

from server import models


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Enum contracts must not connect to a network")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


@pytest.mark.parametrize(
    "model,field,enum,values",
    [
        (models.User, "role", models.Role, "free premium admin"),
        (models.Document, "kind", models.DocumentKind, "docx txt md"),
        (models.Document, "status", models.DocumentStatus, "new queued processing ready"),
        (models.Run, "mode", models.RunMode, "rapido profesional"),
        (
            models.Run,
            "status",
            models.RunStatus,
            "queued processing exporting completed failed canceled",
        ),
        (
            models.RunDocument,
            "status",
            models.RunDocumentStatus,
            "queued processing completed failed",
        ),
        (models.Export, "kind", models.ExportKind, "docx csv jsonl md"),
        (
            models.Suggestion,
            "suggestion_type",
            models.SuggestionType,
            "ortografia puntuacion concordancia estilo lexico otro",
        ),
        (models.Suggestion, "severity", models.SuggestionSeverity, "error warning info"),
        (models.Suggestion, "source", models.SuggestionSource, "rule llm"),
        (models.Suggestion, "status", models.SuggestionStatus, "pending accepted rejected"),
    ],
)
def test_enum_wire_diagnostics_and_database_values(model, field, enum, values):
    expected = values.split()
    assert [member.value for member in enum] == expected
    adapter = TypeAdapter(enum)
    sql_type = model.__table__.columns[field].type
    bind = sql_type.bind_processor(dialect())
    result = sql_type.result_processor(dialect(), None)
    for value in expected:
        member = enum(value)
        assert isinstance(member, str) and member == value
        assert str(member) == f"{enum.__name__}.{member.name}"
        assert f"{member:>30}" == str(member).rjust(30)
        assert json.loads(json.dumps({"value": member})) == {"value": value}
        assert adapter.validate_json(json.dumps(value)) is member
        assert adapter.dump_json(member) == json.dumps(value).encode()
        assert bind(member) == value
        assert result(value) is member
    with pytest.raises(ValueError):
        enum("not-a-supported-value")
