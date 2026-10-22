"""Loads the JSON catalogs in src/backend/data. Reloaded on every call to
`load()` so edits to the JSON files (or a trend refresh) show up immediately."""
import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _read(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=256)
def _skill_reading(task):
    from .exposure_model import predict
    r = predict(task)
    return {"E0": r["E0"], "E1": r["E1"], "E2": r["E2"], "personal": False, "top_words": r["top_words"]}


def load():
    # Model 1 reads every skill's task description once (cached)
    skills = {s["id"]: {**s, "model": _skill_reading(s["task"])} for s in _read("skills.json")["skills"]}
    roles = {r["id"]: r for r in _read("roles.json")["roles"]}
    return {
        "skills": skills,
        "skills_meta": _read("skills.json")["_meta"],
        "roles": roles,
        "roles_meta": _read("roles.json")["_meta"],
        "catalog": _read("pathway_catalog.json")["items"],
        "profiles": _read("profiles.json")["profiles"],
        "assessment": _read("assessment.json"),
        "sdgs": _read("sdgs.json"),
        "signals": _read("signals.json"),
        "trends": _read("trends.json"),
        "facts": _read("malaysia_facts.json")["facts"],
    }
