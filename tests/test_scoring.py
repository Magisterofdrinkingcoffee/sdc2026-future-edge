"""Run: python -m pytest -q"""
import copy

from fastapi.testclient import TestClient

from src.backend import scoring
from src.backend.data_store import load
from src.backend.main import app

DATA = load()
RAVI = next(p for p in DATA["profiles"] if p["id"] == "ravi")


def test_fast_scenario_is_never_better_than_moderate():
    m = scoring.forecast(RAVI["skills"], DATA, "moderate")
    f = scoring.forecast(RAVI["skills"], DATA, "fast")
    mm = {r["role_id"]: r["edge_y3"] for r in m["roles"]}
    for r in f["roles"]:
        assert r["edge_y3"] <= mm[r["role_id"]] + 1e-9


def test_edge_does_not_rise_over_time_without_learning():
    f = scoring.forecast(RAVI["skills"], DATA, "fast")
    for r in f["roles"]:
        edges = [t["edge"] for t in r["timeline"]]
        assert edges == sorted(edges, reverse=True)


def test_trend_data_changes_the_forecast():
    """Judges' success criterion: output visibly changes when trend data changes."""
    before = scoring.forecast(RAVI["skills"], DATA, "moderate")
    data2 = copy.deepcopy(DATA)
    data2["trends"]["signals"]["llm_codegen"]["growth"] = 3.0
    after = scoring.forecast(RAVI["skills"], data2, "moderate")
    b = {r["role_id"]: r["edge_y3"] for r in before["roles"]}
    a = {r["role_id"]: r["edge_y3"] for r in after["roles"]}
    assert a["software_developer"] < b["software_developer"]


def test_completing_steps_raises_edge():
    pw = scoring.one_move_and_pathway(RAVI["skills"], "ai_engineer", DATA, "moderate")
    assert pw["one_move"] and pw["steps"]
    done = [s["id"] for s in pw["steps"][:2]]
    before = scoring.forecast(RAVI["skills"], DATA, goal_role="ai_engineer")["roles"][0]["edge_now"]
    after = scoring.forecast(RAVI["skills"], DATA, goal_role="ai_engineer", completed=done)["roles"][0]["edge_now"]
    assert after > before


def test_pathway_only_uses_catalog_items():
    ids = {i["id"] for i in DATA["catalog"]}
    pw = scoring.one_move_and_pathway(RAVI["skills"], "ai_engineer", DATA, "fast")
    assert all(s["id"] in ids for s in pw["steps"])


def test_catalog_references_are_valid():
    for item in DATA["catalog"]:
        assert all(s in DATA["skills"] for s in item["skills"]), item["id"]
    for role in DATA["roles"].values():
        assert all(s in DATA["skills"] for s in role["skills"]), role["id"]
        assert all(t in DATA["sdgs"]["targets"] for t in role["sdgs"]), role["id"]
    signal_ids = {s["id"] for s in DATA["signals"]["signals"]}
    for s in DATA["skills"].values():
        assert s["signal"] in signal_ids, s["id"]
        assert all(t in DATA["sdgs"]["targets"] for t in s["sdgs"]), s["id"]


def test_assessment_scoring():
    qs = DATA["assessment"]["questions"]
    best = {q["id"]: max(range(len(q["options"])), key=lambda i: q["options"][i]["judgment"] + q["options"][i]["responsibility"]) for q in qs}
    r = scoring.score_assessment(qs, best)
    assert r["judgment"] > 0.8 and r["responsibility"] > 0.8


def test_api_end_to_end():
    c = TestClient(app)
    assert c.get("/api/health").json()["ok"]
    parsed = c.post("/api/profile/parse", json={"text": RAVI["cv_text"]}).json()["skills"]
    assert "python" in parsed
    f = c.post("/api/forecast", json={"skills": RAVI["skills"], "scenario": "fast"}).json()
    assert f["is_estimate"] and f["trend_source"]["source"]
    p = c.post("/api/pathway", json={"skills": RAVI["skills"], "role_id": "ai_engineer"}).json()
    assert p["steps"]
    assert c.post("/api/forecast", json={"skills": {"nope": 1}}).status_code == 400
