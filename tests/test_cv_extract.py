"""Tests for the new CV reader (src/backend/cv_extract.py + gemini_cv.py).

Used by POST /api/profile/upload. PDFs are read with pypdf (no PyMuPDF), and the test PDFs/PNGs
below are built by hand so the tests need no extra packages.

No API key or internet needed: Gemini is faked. All CVs are SYNTHETIC.
"""
import io
import os
import struct
import zipfile
import zlib

import pytest

os.environ.pop("GEMINI_API_KEY", None)
from src.backend import cv_extract, gemini_cv  # noqa: E402
from src.backend.cv_extract import extract_cv  # noqa: E402

os.environ.pop("GEMINI_API_KEY", None)  # cv_extract may load a local .env on import

CV = """Nurul Aina binti Hassan
nurul.synthetic@example.com | 013-222 3333
No. IC: 950101-07-5123
Age: 31   Gender: Female

WORK EXPERIENCE
Data Entry Clerk, DEF Logistics (fictional)
• Data input of shipping orders into SAP
• Reduced downtime by 15% in 2024 - 2025

SKILLS
Excel, SQL, Power BI, Single sign-on setup"""


def _pdf_escape(t):
    return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").replace("•", "-")


def pdf(text=CV, columns=None):
    """Minimal one-page PDF (Helvetica). columns: [((x, y_top), text), ...] in points from the top-left."""
    blocks = columns or [((50, 50), text)]
    ops = []
    for (x, y), t in blocks:
        ops.append(f"BT /F1 10 Tf 12 TL {x} {842 - y} Td")
        ops += [f"({_pdf_escape(line)}) Tj T*" for line in t.splitlines()]
        ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % off for off in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def docx(paragraphs):
    buf = io.BytesIO()
    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", f'<?xml version="1.0"?><w:document {w}><w:body>{body}</w:body></w:document>')
    return buf.getvalue()


def png():
    """A tiny valid PNG (a photo of a CV has no text layer)."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    raw = b"".join(b"\x00" + b"\xff" * 30 for _ in range(10))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 10, 10, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


@pytest.fixture
def fake_gemini(monkeypatch):
    def install(answer):
        monkeypatch.setenv("GEMINI_API_KEY", "fake-for-tests")
        monkeypatch.setattr(gemini_cv, "call_gemini", lambda part: answer)
    return install


def test_personal_data_removed_work_text_kept():
    r = extract_cv(pdf())
    for secret in ["Nurul", "nurul.synthetic", "013-222", "950101", "Age: 31", "Female"]:
        assert secret not in r["raw_text"]
    for kept in ["Data input of shipping orders into SAP", "Reduced downtime by 15% in 2024 - 2025",
                 "Single sign-on setup"]:
        assert kept in r["raw_text"]
    assert {"name", "email", "phone", "ic_number", "age_dob", "gender"} <= set(r["removed_personal_data"])


def test_layout_kept():
    text = extract_cv(pdf())["raw_text"]
    assert "Data input of shipping orders into SAP" in text
    assert "\nSKILLS\n" in text


def test_text_pdf_sends_redacted_text_to_gemini(fake_gemini, monkeypatch):
    """Privacy: for PDFs we can read, Gemini gets the text without personal data, never the file."""
    sent = {}
    def capture(part):
        sent.update(part)
        return {"summary": [], "experience": [], "certifications": [], "projects": [], "skills": ["Excel"], "full_text": ""}
    fake_gemini({})
    monkeypatch.setattr(gemini_cv, "call_gemini", capture)
    extract_cv(pdf())
    assert sent["type"] == "text"
    for secret in ["Nurul", "nurul.synthetic", "013-222", "950101"]:
        assert secret not in sent["text"]


def test_upload_endpoint_reads_word_and_removes_personal_data():
    from fastapi.testclient import TestClient
    from src.backend.main import app
    c = TestClient(app)
    r = c.post("/api/profile/upload", files={"file": ("cv.docx", docx(["Ali bin Abu", "ali@example.com", "SKILLS", "Excel, SQL, Python"]), "application/octet-stream")}).json()
    assert {"sql", "python"} <= set(r["skills"]) and "email" in r["reader"]["removed_personal_data"]
    assert c.post("/api/profile/upload", files={"file": ("cv.doc", b"\xd0\xcf\x11\xe0" + b"\0" * 64, "application/msword")}).status_code == 400


def test_word_docx():
    r = extract_cv(docx(["Ali bin Abu", "SKILLS", "Excel, SQL"]), "cv.docx")
    assert r["format"] == "docx" and "Excel, SQL" in r["raw_text"] and "Ali bin Abu" not in r["raw_text"]


def test_format_detected_without_file_name():
    assert extract_cv(docx(["Ali", "SKILLS", "Excel"]))["format"] == "docx"
    assert extract_cv(png())["format"] == "image"


def test_photo_without_key_flagged():
    r = extract_cv(png(), "cv.png")
    assert r["is_scanned"] and r["raw_text"].strip() == ""


def test_photo_with_gemini(fake_gemini):
    fake_gemini({"summary": [], "experience": [], "certifications": [], "projects": [],
                 "skills": ["Excel"], "full_text": "Ali\nSKILLS: Excel"})
    r = extract_cv(png(), "cv.png")
    assert r["method"].startswith("gemini") and "SKILLS: Excel" in r["raw_text"] and "Ali" not in r["raw_text"]


def test_gemini_invented_phrases_dropped(fake_gemini):
    fake_gemini({"summary": [], "certifications": [], "projects": [], "full_text": "",
                 "experience": ["Data input of shipping orders into SAP"], "skills": ["Excel", "Kubernetes"]})
    r = extract_cv(pdf())
    assert [p["text"] for p in r["rejected_phrases"]] == ["Kubernetes"]


def test_gemini_down_falls_back(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-for-tests")
    def down(part):
        raise gemini_cv.GeminiError("HTTP 503")
    monkeypatch.setattr(gemini_cv, "call_gemini", down)
    r = extract_cv(pdf())
    assert r["method"] == "rules" and "Excel" in r["raw_text"]


def test_old_doc_unsupported():
    assert extract_cv(b"\xd0\xcf\x11\xe0" + b"\0" * 64, "cv.doc")["format"] == "unsupported"


def test_env_inline_comment_and_llm_alias(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("LLM_API_KEY=abc#123 # my key\nLLM_MODEL=gemini-3.8-flash\n")
    monkeypatch.chdir(tmp_path)
    for k in ("GEMINI_API_KEY", "GEMINI_MODEL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    cv_extract._load_dotenv()
    assert os.environ["GEMINI_API_KEY"] == "abc#123" and os.environ["GEMINI_MODEL"] == "gemini-3.8-flash"
