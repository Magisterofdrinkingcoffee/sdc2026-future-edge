"""CV extraction: PDF / Word / photo / text -> clean text -> sections -> phrases for skill matching.

Author: Alibek Berikov (PR #1). PDF reading switched from PyMuPDF (AGPL-3.0) to pypdf (BSD)
so the project stays compatible with its Apache-2.0 licence.

Output contract (what the matching step receives):
{
  "source": "aiman_cv.pdf",
  "pages": 1,
  "is_scanned": false,
  "raw_text": "...",
  "sections": {"summary": "...", "experience": "...", "skills": "...", ...},
  "phrases": [{"text": "Fix machines when they break down", "section": "experience", "page": 1}, ...],
  "removed_personal_data": ["email", "phone"],
  "warnings": []
}

Every phrase is copied verbatim from the CV (never generated), so later steps cannot
invent skills. Personal data (name line, email, phone, IC number, age, gender, DOB)
is removed before matching: privacy + fairness (matching never sees age/gender).

Usage:
    python cv_extract.py path/to/cv.pdf            # prints JSON
    from cv_extract import extract_cv
    result = extract_cv("cv.pdf")                   # from a file path
    result = extract_cv(uploaded_bytes, "cv.pdf")   # from a web upload
"""

import json
import os
import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader  # BSD licence


def _load_dotenv():
    """Read keys from a local .env file (never committed) in the project root or current folder."""
    here = Path(__file__).resolve().parent
    for folder in [Path.cwd(), here, *here.parents][:6]:
        env = folder / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    v = re.split(r"\s+#", v, maxsplit=1)[0]  # drop "# comment" on the same line
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break
    # the team's .env.example uses LLM_API_KEY / LLM_MODEL - accept those names too
    if not os.getenv("GEMINI_API_KEY") and os.getenv("LLM_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["LLM_API_KEY"]
    if not os.getenv("GEMINI_MODEL") and (os.getenv("LLM_MODEL") or "").startswith("gemini"):
        os.environ["GEMINI_MODEL"] = os.environ["LLM_MODEL"]


_load_dotenv()

MAX_GEMINI_BYTES = 18 * 1024 * 1024  # Gemini inline limit is 20MB per request
IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
              ".heic": "image/heic", ".heif": "image/heif"}


def detect_format(data_bytes, filename):
    """Return (kind, mime). Looks at the file's first bytes, not only the extension."""
    head = data_bytes[:16]
    ext = Path(filename).suffix.lower()
    if head.startswith(b"%PDF"):
        return "pdf", "application/pdf"
    if head.startswith(b"\x89PNG"):
        return "image", "image/png"
    if head.startswith(b"\xff\xd8"):
        return "image", "image/jpeg"
    if head[:4] == b"RIFF" and data_bytes[8:12] == b"WEBP":
        return "image", "image/webp"
    if data_bytes[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftypheif"):
        return "image", IMAGE_MIME.get(ext, "image/heic")
    if head.startswith(b"PK"):
        try:
            if "word/document.xml" in zipfile.ZipFile(BytesIO(data_bytes)).namelist():
                return "docx", "text/plain"
        except zipfile.BadZipFile:
            pass
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return "unsupported", "old .doc format - please save as .docx or PDF"
    if ext in (".txt", ".md"):
        return "txt", "text/plain"
    try:
        data_bytes.decode("utf-8")
        return "txt", "text/plain"
    except UnicodeDecodeError:
        return "unsupported", f"unknown file type ({ext or 'no extension'})"


def read_docx(data_bytes):
    """Word .docx -> text, one paragraph per line (includes tables and text boxes). Standard library only."""
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    xml = zipfile.ZipFile(BytesIO(data_bytes)).read("word/document.xml")
    root = ElementTree.fromstring(xml)
    lines = []
    for para in root.iter(f"{W}p"):
        text = "".join(t.text or "" for t in para.iter(f"{W}t"))
        if text.strip():
            lines.append(text)
    return "\n".join(lines)

# Headings in English and Bahasa Malaysia -> normalised section name
SECTION_HEADINGS = {
    "summary": ["summary", "profile", "about me", "objective", "career objective", "ringkasan", "profil", "objektif"],
    "experience": ["experience", "work experience", "employment history", "work history", "professional experience",
                   "pengalaman", "pengalaman kerja"],
    "skills": ["skills", "technical skills", "key skills", "competencies", "core skills", "kemahiran"],
    "education": ["education", "academic background", "qualifications", "pendidikan", "kelayakan akademik"],
    "certifications": ["certifications", "certificates", "licenses", "training", "courses", "sijil", "latihan",
                       "kursus"],
    "languages": ["languages", "bahasa"],
    "projects": ["projects", "projek"],
}
HEADING_LOOKUP = {h: name for name, hs in SECTION_HEADINGS.items() for h in hs}

# Sections whose lines become phrases for skill matching
MATCH_SECTIONS = {"summary", "experience", "skills", "certifications", "projects", "other"}

# Label-based patterns, so normal sentences ("Single sign-on", "2024 - 2025") are not removed
PERSONAL_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "phone": re.compile(
        r"(\+?60[\s-]?|\b0)1\d[\s-]?\d{3,4}[\s-]?\d{4}\b"      # Malaysian mobile: 012-345 6789, +60 16 555 1234
        r"|(\+?60[\s-]?|\b0)[3-9][\s-]?\d{3,4}[\s-]?\d{4}\b"   # Malaysian landline: 03-1234 5678
        r"|\+\d{1,3}[\s-]?\(?\d{1,4}\)?([\s-]?\d{2,4}){2,4}"   # international: +65 6123 4567
        r"|\b(phone|tel|telefon|mobile|h/p)\s*[:.]", re.I),
    "ic_number": re.compile(r"\b\d{6}-\d{2}-\d{4}\b|\b(no\.?\s*)?(ic|mykad|kad pengenalan)\s*[:.]", re.I),
    "age_dob": re.compile(r"\b(age|umur)\s*[:\-]?\s*\d|\b(date of birth|dob|tarikh lahir|born on)\b", re.I),
    "gender": re.compile(r"\b(gender|jantina|sex)\s*[:\-]|^(male|female|lelaki|perempuan)$", re.I),
    "marital": re.compile(r"\b(marital status|status perkahwinan)\b|^(single|married|bujang|berkahwin)$", re.I),
}
# Lines at the top of a CV that are titles, not the person's name
TITLE_LINES = {"curriculum vitae", "resume", "résumé", "cv", "biodata", "personal details", "maklumat peribadi"}
# Bullet characters, including ones Word/PDF fonts often map to "?", U+FFFD or private-use glyphs
BULLETS = "•●▪■◦‣∙·-–—*>?�"
DATE_ONLY = re.compile(r"^[\d\s/\-–—.,]*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|present|now|kini)?[\w\s/\-–—.,]*\d{4}[\s\-–—]*(present|now|kini|\d{4})?$", re.I)


# ---------------- reading the PDF ----------------
def read_pdf(data, filename="cv.pdf"):
    """PDF -> list of page texts (pypdf). Multi-column layouts are read line by line;
    Gemini mode handles complex layouts better."""
    reader = PdfReader(str(data) if isinstance(data, (str, Path)) else BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return pages, len(pages)


# ---------------- cleaning ----------------
def _clean_line(line):
    line = line.replace(" ", " ").replace("ﬁ", "fi").replace("ﬂ", "fl")
    line = re.sub(r"\s+", " ", line).strip()
    return line.lstrip(BULLETS).strip()


def _is_heading(line):
    key = line.lower().strip(" :").strip()
    # "Skills & Tools", "Technical Skills and Technologies" -> "skills", "technical skills"
    key = re.sub(r"\s*(&|and|dan)\s*(tools|technologies|competencies|abilities|alat)$", "", key)
    return HEADING_LOOKUP.get(key) if len(key.split()) <= 4 else None


def _personal_hits(line):
    return [name for name, pat in PERSONAL_PATTERNS.items() if pat.search(line)]


def redact_text(text):
    """CV text with the name line and lines containing personal data removed.

    Keeps the layout (line breaks, blank lines, bullets) so later sentence splitting still works;
    broken bullet glyphs ("?", U+FFFD, Word symbols) are turned into a normal "•".
    """
    out, name_done = [], False
    for raw in text.splitlines():
        line = _clean_line(raw)
        if not line:
            out.append("")
            continue
        if not name_done:
            if line.lower().strip(" :") in TITLE_LINES:
                continue
            name_done = True
            if len(line.split()) <= 6 and not _is_heading(line):
                continue
        if _personal_hits(line):
            continue
        stripped = raw.strip()
        if stripped and stripped[0] in BULLETS and stripped[0] not in "-*>":
            raw = "• " + stripped[1:].lstrip()
        out.append(raw.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


# ---------------- main ----------------
def extract_cv_rules(data, filename=None):
    filename = filename or (Path(data).name if isinstance(data, (str, Path)) else "upload.pdf")
    data_bytes = Path(data).read_bytes() if isinstance(data, (str, Path)) else data
    warnings, removed = [], set()
    kind, mime = detect_format(data_bytes, filename)

    if kind == "pdf":
        page_texts, n_pages = read_pdf(data_bytes, "cv.pdf")
    elif kind == "docx":
        page_texts, n_pages = [read_docx(data_bytes)], 1
    elif kind == "txt":
        page_texts, n_pages = [data_bytes.decode("utf-8", "ignore")], 1
    else:  # image or unsupported: no text layer
        page_texts, n_pages = [""], 1
        if kind == "unsupported":
            warnings.append(f"Cannot read this file: {mime}.")

    raw_text = "\n".join(page_texts)
    is_scanned = kind in ("pdf", "image") and len(raw_text.strip()) < 50
    if is_scanned:
        warnings.append("No text layer (scan or photo). Gemini mode can read it; "
                        "rules mode cannot - ask the user to use the form.")

    sections, phrases = {}, []
    current = "other"
    first_line_seen = False
    for page_no, page_text in enumerate(page_texts, 1):
        for raw in page_text.splitlines():
            line = _clean_line(raw)
            if not line:
                continue
            if not first_line_seen:
                if line.lower().strip(" :") in TITLE_LINES:
                    continue  # skip "CURRICULUM VITAE"; the next line is the name
                first_line_seen = True
                # First line of a CV is almost always the person's name -> drop it
                if len(line.split()) <= 6 and not _is_heading(line):
                    removed.add("name")
                    continue
            heading = _is_heading(line)
            if heading:
                current = heading
                continue
            hits = _personal_hits(line)
            if hits:
                removed.update(hits)
                continue
            sections.setdefault(current, []).append(line)

            if current not in MATCH_SECTIONS or DATE_ONLY.match(line):
                continue
            # Skills sections are usually comma/pipe separated lists -> split them
            parts = re.split(r"[,|;/]", line) if current == "skills" else [line]
            for part in parts:
                part = part.strip(" .:")
                if 1 <= len(part.split()) <= 15 and len(part) > 2:
                    phrases.append({"text": part, "section": current, "page": page_no})

    if not phrases and not is_scanned:
        warnings.append("No skill phrases found - check the CV layout or use the form.")

    return {
        "source": filename,
        "format": kind,
        "method": "rules",
        "pages": n_pages,
        "is_scanned": is_scanned,
        "raw_text": redact_text(raw_text),
        "_full_text": raw_text,  # internal, used only to verify Gemini phrases; removed before returning
        "sections": {k: "\n".join(v) for k, v in sections.items()},
        "phrases": phrases,
        "rejected_phrases": [],
        "removed_personal_data": sorted(removed),
        "warnings": warnings,
    }


def extract_cv(data, filename=None, method=None):
    """Main entry point.

    method="gemini": Gemini reads the CV, phrases are verified against the real text.
    method="rules":  PyMuPDF + our rules only (free, offline).
    Default: Gemini if GEMINI_API_KEY is set, otherwise rules. If Gemini fails, falls back to rules.
    """
    filename = filename or (Path(data).name if isinstance(data, (str, Path)) else "upload.pdf")
    rules_result = extract_cv_rules(data, filename)
    method = method or ("gemini" if os.getenv("GEMINI_API_KEY") else "rules")
    kind = rules_result["format"]
    if method != "gemini" or kind == "unsupported":
        rules_result.pop("_full_text", None)
        return rules_result

    try:
        from . import gemini_cv
    except ImportError:
        import gemini_cv
    file_bytes = Path(data).read_bytes() if isinstance(data, (str, Path)) else data
    if kind in ("docx", "txt") or (kind == "pdf" and not rules_result["is_scanned"]):
        # Privacy: when we can read the text ourselves, Gemini only gets the text with personal data removed.
        # Only scans and photos (no text layer) are sent as the original file.
        part = {"type": "text", "text": "CV TEXT:\n" + rules_result["raw_text"]}
    elif len(file_bytes) > MAX_GEMINI_BYTES:
        rules_result["warnings"].append("File is larger than 18MB - too big for Gemini; used rules.")
        rules_result.pop("_full_text", None)
        return rules_result
    elif kind == "image":
        part = {"type": "image", "data": file_bytes, "mime_type": detect_format(file_bytes, filename)[1]}
    else:
        part = {"type": "document", "data": file_bytes, "mime_type": "application/pdf"}
    try:
        answer = gemini_cv.call_gemini(part)
    except Exception as e:
        rules_result["warnings"].append(f"Gemini unavailable ({e}); used rules instead.")
        rules_result.pop("_full_text", None)
        return rules_result

    full_text = rules_result.pop("_full_text", "")
    kept, rejected = gemini_cv.verify(answer, "" if rules_result["is_scanned"] else full_text)
    # Safety net: drop anything that still looks like personal data
    removed = set(rules_result["removed_personal_data"])
    phrases = []
    for p in kept:
        hits = _personal_hits(p["text"])
        if hits:
            removed.update(hits)
        else:
            phrases.append(p)

    warnings = list(rules_result["warnings"]) if not rules_result["is_scanned"] else []
    if rules_result["is_scanned"]:
        warnings.append("Scanned CV: read by Gemini, checked against its own transcription. "
                        "Ask the user to confirm the skills.")
    if rejected:
        warnings.append(f"{len(rejected)} phrase(s) from Gemini were not in the CV and were removed.")

    sections = {}
    for p in phrases:
        sections.setdefault(p["section"], []).append(p["text"])
    return {
        **rules_result,
        "method": f"gemini ({gemini_cv.MODEL})",
        "raw_text": rules_result["raw_text"] or redact_text(answer.get("full_text", "")),
        "sections": {k: "\n".join(v) for k, v in sections.items()},
        "phrases": phrases,
        "rejected_phrases": rejected,
        "removed_personal_data": sorted(removed),
        "warnings": warnings,
    }


def phrases_for_matching(result):
    """What the matching engine needs: just the phrase strings, no duplicates."""
    seen, out = set(), []
    for p in result["phrases"]:
        key = p["text"].lower()
        if key not in seen:
            seen.add(key)
            out.append(p["text"])
    return out


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("usage: python cv_extract.py path/to/cv (pdf/docx/jpg/png/txt) [gemini|rules]")
    method = sys.argv[2] if len(sys.argv) == 3 else None
    print(json.dumps(extract_cv(sys.argv[1], method=method), indent=2, ensure_ascii=False))
