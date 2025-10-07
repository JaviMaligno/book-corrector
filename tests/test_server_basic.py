from __future__ import annotations

import io
import os
import types

import pytest


@pytest.fixture(scope="module")
def app():
    # Ensure demo plan is deterministic for tests
    os.environ["DEMO_PLAN"] = "premium"
    try:
        from server.main import create_app

        return create_app()
    except RuntimeError:
        pytest.skip("FastAPI not installed in this environment")


@pytest.fixture()
def client(app):
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("FastAPI test client not available")
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_limits_premium(client):
    r = client.get("/me/limits")
    assert r.status_code == 200
    data = r.json()
    assert data["plan"] == "premium"
    assert data["ai_enabled"] is True


def test_create_run_queue_and_status(client):
    # Register user and get token
    rr = client.post("/auth/register", json={"email": "user@example.com", "password": "secret123"})
    if rr.status_code != 200:
        # If already exists, login
        rr = client.post("/auth/login", json={"email": "user@example.com", "password": "secret123"})
        assert rr.status_code == 200
    token = rr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a project
    pr = client.post("/projects", json={"name": "Proyecto 1", "lang_variant": "es-ES"}, headers=headers)
    assert pr.status_code == 200
    project_id = pr.json()["id"]

    # Upload a few documents
    files = [
        ("files", ("cap1.txt", io.BytesIO(b"Hola mundo."), "text/plain")),
        ("files", ("cap2.txt", io.BytesIO(b"Otra pagina."), "text/plain")),
        ("files", ("cap3.md", io.BytesIO(b"# Titulo\nTexto."), "text/markdown")),
    ]
    ur = client.post(f"/projects/{project_id}/documents/upload", files=files, headers=headers)
    assert ur.status_code == 200
    uploaded = ur.json()
    assert len(uploaded) == 3
    doc_ids = [d["id"] for d in uploaded]

    # Create a run with document IDs
    body = {
        "project_id": project_id,
        "document_ids": doc_ids,
        "mode": "rapido",
        "use_ai": True,
    }
    r = client.post("/runs", json=body, headers=headers)
    assert r.status_code == 200
    res = r.json()
    assert "run_id" in res
    assert isinstance(res["accepted_documents"], list)
    assert res["queued"] >= 0

    # Poll status until completed or timeout
    import time
    for _ in range(50):
        r2 = client.get(f"/runs/{res['run_id']}", headers=headers)
        assert r2.status_code == 200
        st = r2.json()
        if st["status"] == "completed":
            break
        time.sleep(0.1)
    # List exports
    le = client.get(f"/runs/{res['run_id']}/exports", headers=headers)
    assert le.status_code == 200
    exports = le.json()
    assert isinstance(exports, list)
    cats = {e["category"] for e in exports}
    # Verify core artifacts exist
    assert "corrected" in cats
    assert "log_jsonl" in cats
    assert "report_docx" in cats
    # Verify new persistent exports
    assert "changelog_csv" in cats
    assert "summary_md" in cats

    # Direct endpoints for CSV and summary
    dl_csv = client.get(f"/runs/{res['run_id']}/changelog.csv", headers=headers)
    assert dl_csv.status_code == 200
    assert dl_csv.content and len(dl_csv.content) > 0

    dl_sum = client.get(f"/runs/{res['run_id']}/summary.md", headers=headers)
    assert dl_sum.status_code == 200
    assert b"Carta de edici" in dl_sum.content  # substring tolerant to accents encoding
