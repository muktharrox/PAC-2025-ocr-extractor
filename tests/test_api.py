import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("fpdf")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from tools.generate_synthetic_docs import build_pdf_bytes  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "ocr_engines_available" in body


def test_extract_pj():
    data = build_pdf_bytes("pj")
    r = client.post("/api/v1/extract", files={"file": ("doc.pdf", data, "application/pdf")})
    assert r.status_code == 200
    body = r.json()
    assert body["document_type"] == "RGP_PJ"
    assert body["data"]["numero_rgp"] == "SC-0004633-8"
    assert body["status"] in ("APPROVED", "REVIEW_REQUIRED")


def test_extract_rejeita_tipo_invalido():
    r = client.post(
        "/api/v1/extract",
        files={"file": ("x.exe", b"MZ\x90\x00 nao e um pdf", "application/octet-stream")},
    )
    assert r.status_code in (400, 415, 422)


def test_get_e_corrige_campo():
    data = build_pdf_bytes("pf")
    r = client.post("/api/v1/extract", files={"file": ("doc.pdf", data, "application/pdf")})
    doc_id = r.json()["document_id"]

    r2 = client.get(f"/api/v1/documents/{doc_id}")
    assert r2.status_code == 200

    r3 = client.put(
        f"/api/v1/documents/{doc_id}/fields/numero_rgp",
        json={"value": "SC-0004633-8", "reviewed_by": "tester@empresa.com"},
    )
    assert r3.status_code == 200


def test_get_inexistente():
    r = client.get("/api/v1/documents/nao-existe")
    assert r.status_code == 404
