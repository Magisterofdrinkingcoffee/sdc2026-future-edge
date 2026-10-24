"""CV parsing: PDF -> text -> skills with a level and the evidence sentence.

Only skills that exist in data/skills.json can be returned, so the parser can
never invent a skill. Every skill comes with the sentence it was found in, so
the user (and judges) can see WHY it was detected.

File reading and personal-data removal live in cv_extract.py (Alibek's module); this file turns text into skills.
"""
import io
import re

from pypdf import PdfReader

STRONG = ("led ", "lead ", "built", "developed", "designed", "deployed", "managed", "trained",
          "internship", "intern ", "years", "responsible", "professional", "certified", "president", "won ")
MEDIUM = ("project", "coursework", "course", "completed", "assisted", "member", "elective", "prepares", "maintain")
WEAK = ("basic", "familiar", "beginner", "some ", "currently learning", "still learning")


def extract_text(pdf_bytes: bytes) -> str:
    """The ONLY place that reads PDFs."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _sentences(text):
    # A short line without punctuation (e.g. "Experience", "Projects") is a section heading: keep it separate.
    text = re.sub(r"^\s*([A-Z][\w&/ ]{0,30})\s*$", r"\n\1\n", text, flags=re.M)
    # PDFs break lines mid-sentence: join wrapped lines, keep blank lines / bullets as breaks
    text = re.sub(r"(?<![.!?:])\n(?!\s*[•\-\n])", " ", text)
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip(" •-\t\x7f") for p in parts if len(p.strip(" \x7f")) > 3]


def _level(sentence):
    s = sentence.lower() + " "
    if any(w in s for w in WEAK):
        return 0.3, "basic"
    if any(w in s for w in STRONG):
        return 0.7, "hands-on experience"
    if any(w in s for w in MEDIUM):
        return 0.5, "coursework / project"
    return 0.4, "mentioned"


def parse_skills(text, catalog):
    """Returns {skill_id: {"level", "reason", "evidence"}} for skills found in text."""
    found = {}
    sents = _sentences(text)
    for skill in catalog.values():
        aliases = sorted({skill["name"].lower(), *skill["aliases"]}, key=len, reverse=True)
        hits = []
        for sent in sents:
            low = sent.lower()
            if any(re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", low) for a in aliases):
                hits.append(sent)
        if not hits:
            continue
        scored = [(_level(h), h) for h in hits]
        (lvl, reason), best = max(scored, key=lambda x: x[0][0])
        lvl = min(0.9, lvl + 0.05 * (len(hits) - 1))  # mentioned several times -> a bit stronger
        found[skill["id"]] = {"level": round(lvl, 2), "reason": reason, "evidence": best[:180], "mentions": len(hits)}
    return found
