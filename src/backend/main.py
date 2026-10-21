"""Future Edge – FastAPI backend.

Run locally:  uvicorn src.backend.main:app --reload --port 8000
"""
import copy
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import scoring, trends
from .cv_parser import extract_text, parse_skills
from .data_store import DATA_DIR, load

SAMPLE_CVS = DATA_DIR / "sample_cvs"

app = FastAPI(title="Future Edge API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------------ models
class Assessment(BaseModel):
    judgment: Optional[float] = None
    responsibility: Optional[float] = None


class ProfileIn(BaseModel):
    skills: Dict[str, float] = Field(default_factory=dict, description="skill_id -> proficiency 0-1")
    scenario: str = "moderate"
    assessment: Optional[Assessment] = None
    goal_role: Optional[str] = None
    completed: List[str] = Field(default_factory=list, description="ids of finished pathway steps")
    signal_overrides: Dict[str, float] = Field(default_factory=dict, description="what-if: signal_id -> growth")


class PathwayIn(ProfileIn):
    role_id: str
    hours_per_week: float = 6


class ParseIn(BaseModel):
    text: str


class AnswersIn(BaseModel):
    answers: Dict[str, int]


def _data(overrides=None):
    data = load()
    if overrides:
        data = copy.deepcopy(data)
        for sid, g in overrides.items():
            if sid in data["trends"]["signals"]:
                data["trends"]["signals"][sid]["growth"] = g
        data["trends"]["source"] = (data["trends"].get("source") or "") + " + WHAT-IF overrides set by user"
    return data


def _check(scenario, skills, data):
    if scenario not in scoring.SCENARIOS:
        raise HTTPException(400, f"scenario must be one of {list(scoring.SCENARIOS)}")
    unknown = [s for s in skills if s not in data["skills"]]
    if unknown:
        raise HTTPException(400, f"unknown skills: {unknown}")


# ------------------------------------------------------------------ routes
@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/meta")
def meta():
    d = load()
    return {
        "profiles": d["profiles"],
        "roles": [{"id": r["id"], "title": r["title"], "field": r["field"], "outlook": r.get("outlook"),
                   "mycol": r.get("mycol"), "wage": r.get("wage")} for r in d["roles"].values()],
        "facts": d["facts"],
        "roles_sources": d["roles_meta"].get("sources"),
        "skills": [{"id": s["id"], "name": s["name"], "category": s["category"]} for s in d["skills"].values()],
        "scenarios": scoring.SCENARIOS,
        "sdgs": d["sdgs"],
        "signals": d["signals"]["signals"],
        "weights": {"base": scoring.W_BASE, "human": scoring.W_HUMAN, "rarity": scoring.W_RARITY},
        "llm": None,  # set to the model name once an LLM is wired in (must be declared in Tech Declaration)
    }


def _parsed(text, source):
    d = load()
    found = parse_skills(text, d["skills"])
    for sid, f in found.items():
        f["name"] = d["skills"][sid]["name"]
        f["category"] = d["skills"][sid]["category"]
    return {"skills": found, "source": source, "chars": len(text),
            "method": "Keyword + context rules against our skill catalog (skills.json). The parser can only return catalog skills.",
            "note": "Levels are a first guess from the wording of your CV – adjust them if they're wrong."}


@app.post("/api/profile/parse")
def parse_profile(body: ParseIn):
    """Parse pasted CV text."""
    return _parsed(body.text, "pasted text")


@app.post("/api/profile/upload")
async def upload_cv(file: UploadFile = File(...)):
    """Parse an uploaded PDF CV. Nothing is stored – the file is read in memory and discarded."""
    raw = await file.read()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "PDF too large (max 5 MB)")
    try:
        text = extract_text(raw)
    except Exception:
        raise HTTPException(400, "Could not read this PDF. Try another file or paste the text instead.")
    if len(text.strip()) < 20:
        raise HTTPException(400, "This PDF has no readable text (maybe it's a scanned image). Paste the text instead.")
    return _parsed(text, file.filename or "uploaded PDF")


@app.get("/api/sample-cvs/{profile_id}.pdf")
def sample_cv(profile_id: str):
    f = SAMPLE_CVS / f"{profile_id}.pdf"
    if not re.fullmatch(r"[a-z]+", profile_id) or not f.is_file():
        raise HTTPException(404, "no such sample CV")
    return FileResponse(f, media_type="application/pdf", filename=f"{profile_id}-sample-cv.pdf")


@app.get("/api/assessment")
def get_assessment():
    a = load()["assessment"]
    return {"questions": [{"id": q["id"], "text": q["text"], "options": [o["text"] for o in q["options"]]} for q in a["questions"]],
            "note": "Your results are estimates to guide you – never a hiring decision."}


@app.post("/api/assessment")
def post_assessment(body: AnswersIn):
    return scoring.score_assessment(load()["assessment"]["questions"], body.answers)


@app.post("/api/forecast")
def forecast(body: ProfileIn):
    d = _data(body.signal_overrides)
    _check(body.scenario, body.skills, d)
    return scoring.forecast(body.skills, d, body.scenario,
                            body.assessment.model_dump() if body.assessment else None,
                            body.goal_role, body.completed)


@app.post("/api/pathway")
def pathway(body: PathwayIn):
    d = _data(body.signal_overrides)
    _check(body.scenario, body.skills, d)
    if body.role_id not in d["roles"]:
        raise HTTPException(404, "unknown role")
    return scoring.one_move_and_pathway(body.skills, body.role_id, d, body.scenario,
                                        body.assessment.model_dump() if body.assessment else None,
                                        body.completed, body.hours_per_week)


# ------------------------------------------------------------------ trends
_refresh = {"running": False, "log": [], "error": None}


def _run_refresh():
    _refresh.update(running=True, log=[], error=None)
    try:
        trends.refresh(progress=_refresh["log"].append)
    except Exception as e:  # fallback: keep the last cached trends.json
        _refresh["error"] = f"Refresh failed ({e}). Still using the cached data shown below."
    finally:
        _refresh["running"] = False


@app.get("/api/trends")
def get_trends():
    return {**load()["trends"], "refresh": _refresh}


@app.post("/api/trends/refresh")
def refresh_trends():
    if not _refresh["running"]:
        threading.Thread(target=_run_refresh, daemon=True).start()
    return {"started": True}


# ------------------------------------------------------------------ frontend
DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "unknown API route")
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")
