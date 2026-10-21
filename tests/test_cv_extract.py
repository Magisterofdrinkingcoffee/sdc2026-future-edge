"""Tests for the new CV reader (src/backend/cv_extract.py + gemini_cv.py).

The module is not wired into the app yet; to use it, replace the body of
cv_parser.extract_text() with:   return extract_cv(pdf_bytes)["raw_text"]
and add "pymupdf" to requirements.txt.

No API key or internet needed: Gemini is faked. All CVs are SYNTHETIC.
"""
import io
import os
import zipfile

import pytest

pymupdf = pytest.importorskip("pymupdf")  # skipped (not failed) if pymupdf isn't installed yet

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


def pdf(text=CV, columns=None):
    doc = pymupdf.open()
    page = doc.new_page()
    for rect, t in (columns or [((50, 50, 550, 800), text)]):
        page.insert_textbox(pymupdf.Rect(*rect), t, fontsize=10)
    return doc.tobytes()


def docx(paragraphs):
    buf = io.BytesIO()
    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", f'<?xml version="1.0"?><w:document {w}><w:body>{body}</w:body></w:document>')
    return buf.getvalue()


def png():
    src = pymupdf.open()
    src.new_page().insert_text((50, 50), "SKILLS: Excel", fontsize=12)
    return src[0].get_pixmap(dpi=60).tobytes("png")


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
    assert "• Data input of shipping orders into SAP" in text
    assert "\nSKILLS\n" in text


def test_two_columns():
    text = extract_cv(pdf(columns=[
        ((40, 40, 560, 80), "Lim Wei Jie\nwei@example.com"),
        ((40, 100, 250, 800), "SKILLS\nHydraulics, Pneumatics"),
        ((300, 100, 560, 800), "WORK EXPERIENCE\n• Machinery repair for stamping presses"),
    ]))["raw_text"]
    assert text.index("Hydraulics") < text.index("Machinery repair")
    assert "Lim Wei Jie" not in text


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
