"""Read a CV with Gemini (sees the whole document: Canva, tables, scans, icons).

Gemini only proposes phrases. Every phrase is then checked against the CV's real text,
and anything not found there is rejected, so the AI cannot add skills the person never wrote.

Needs GEMINI_API_KEY (free key from https://aistudio.google.com). Model can be changed with
GEMINI_MODEL. Uses the Gemini Interactions API over plain HTTPS (no extra packages).
"""

import base64
import json
import os
import re
import urllib.error
import urllib.request
from difflib import SequenceMatcher

API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
SECTIONS = ["summary", "experience", "skills", "certifications", "projects"]

PROMPT = """You are extracting information from a CV for a career-matching tool.

Rules:
- Copy phrases EXACTLY as written in the CV. Do not rephrase, translate, summarise or add anything.
- Do NOT infer skills that are not written. If unsure, leave it out.
- Do NOT return personal data: no name, email, phone, address, IC number, age, date of birth,
  gender, race, religion, marital status or photo descriptions.
- "skills": one item per skill (split comma or pipe separated lists).
- "experience": job titles and each duty/achievement line, one item each. Skip lines that are only dates.
- "full_text": the full visible text of the CV in reading order (this is used to verify your phrases).
"""

SCHEMA = {
    "type": "object",
    "properties": {
        **{s: {"type": "array", "items": {"type": "string"}} for s in SECTIONS},
        "full_text": {"type": "string"},
    },
    "required": SECTIONS + ["full_text"],
}


class GeminiError(RuntimeError):
    pass


def available():
    return bool(os.getenv("GEMINI_API_KEY"))


def ask_json(parts, prompt, schema, timeout=90):
    """Generic call: send parts + instruction, get back a dict that follows `schema`.

    parts: list of {"type": "document"|"image", "data": bytes, "mime_type": ...} or {"type": "text", "text": ...}
    """
    if not available():
        raise GeminiError("GEMINI_API_KEY is not set")
    clean = []
    for p in parts:
        if isinstance(p.get("data"), (bytes, bytearray)):
            p = {**p, "data": base64.b64encode(p["data"]).decode()}
        clean.append(p)
    body = {
        "model": MODEL,
        "input": clean + [{"type": "text", "text": prompt}],
        "response_format": {"type": "text", "mime_type": "application/json", "schema": schema},
    }
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode(), headers={
        "x-goog-api-key": os.environ["GEMINI_API_KEY"],
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:400]
        raise GeminiError(f"HTTP {e.code} from Gemini: {detail}") from e
    except urllib.error.URLError as e:
        raise GeminiError(f"Cannot reach Gemini: {e.reason}") from e
    try:
        return json.loads(_find_text(data))
    except (ValueError, json.JSONDecodeError) as e:
        raise GeminiError(f"Unexpected Gemini response: {str(data)[:400]}") from e


def call_gemini(part):
    """Read one CV (document, image or text part) and return the extracted sections."""
    return ask_json([part], PROMPT, SCHEMA)


def _find_text(data):
    """Pull the model's text out of the response (steps[-1].content[0].text, per the docs)."""
    try:
        return data["steps"][-1]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        pass
    # Fallback: first string that looks like a JSON object anywhere in the response
    stack = [data]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, str) and item.strip().startswith("{"):
            return item
    raise ValueError(f"No text in Gemini response: {str(data)[:300]}")


# ---------------- verification: no invented phrases ----------------
def _norm(s):
    return re.sub(r"[^\w%+#.]+", " ", s.lower()).strip()


def appears_in(phrase, source_norm, min_ratio=0.9):
    """True if the phrase (almost) literally appears in the CV text."""
    p = _norm(phrase)
    if not p:
        return False
    if p in source_norm:
        return True
    # tolerate small differences (line breaks, hyphenation, a missing character)
    m = SequenceMatcher(None, source_norm, p, autojunk=False).find_longest_match(0, len(source_norm), 0, len(p))
    return m.size / len(p) >= min_ratio


def verify(answer, pdf_text):
    """Keep only phrases that exist in the CV. For scans (no PDF text) we can only check
    against Gemini's own transcription, so those are marked as less certain."""
    has_pdf_text = bool(pdf_text.strip())  # caller passes "" for scans/photos
    source = pdf_text if has_pdf_text else answer.get("full_text", "")
    source_norm = _norm(source)
    kept, rejected = [], []
    for section in SECTIONS:
        for phrase in answer.get(section, []) or []:
            # strip bullets and broken bullet glyphs ("?", U+FFFD, Word private-use symbols)
            phrase = re.sub(r"\s+", " ", phrase).strip().lstrip("•●▪■◦‣∙·-–—*>?\ufffd\uf0b7\uf0a7\uf076\uf0d8\uf0fc ").strip(" .:")
            if not phrase:
                continue
            if appears_in(phrase, source_norm):
                kept.append({"text": phrase, "section": section, "page": None,
                             "verified_against": "pdf_text" if has_pdf_text else "gemini_transcription"})
            else:
                rejected.append({"text": phrase, "section": section, "reason": "not found in CV text"})
    return kept, rejected
