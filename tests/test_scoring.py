"""Run: python -m pytest -q"""
import copy

from fastapi.testclient import TestClient

from src.backend import scoring
from src.backend.cv_parser import extract_text, parse_skills
from src.backend.data_store import DATA_DIR, load
from src.backend.main import app

DATA = load()
_pdf = (DATA_DIR / "sample_cvs" / "ravi.pdf").read_bytes()
RAVI = {"skills": {k: v["level"] for k, v in parse_skills(extract_text(_pdf), DATA["skills"]).items()}}


def test_fast_scenario_is_never_better_than_moderate():
    m = scoring.forecast(RAVI["skills"], DATA, "moderate")
    f = scoring.forecast(RAVI["skills"], DATA, "fast")
    mm = {r["role_id"]: r["edge_y3"] for r in m["roles"]}
    for r in f["roles"]:
        assert r["edge_y3"] <= mm[r["role_id"]] + 1e-9


def test_edge_does_not_rise_over_time_without_learning():
    """With a flat or shrinking job market, AI progress alone can only lower your edge.
    (In a growing market the score may rise – that is the WEF demand data at work.)"""
    f = scoring.forecast(RAVI["skills"], DATA, "fast")
    for r in f["roles"]:
        if all(t["market"] <= 1 for t in r["timeline"]):
            edges = [t["edge"] for t in r["timeline"]]
            assert edges == sorted(edges, reverse=True), r["role_id"]


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
    pw = scoring.one_move_and_pathway(RAVI["skills"], "ai_ml_specialist", DATA, "moderate")
    assert pw["one_move"] and pw["steps"]
    done = [s["id"] for s in pw["steps"][:2]]
    before = scoring.forecast(RAVI["skills"], DATA, goal_role="ai_ml_specialist")["roles"][0]["edge_now"]
    after = scoring.forecast(RAVI["skills"], DATA, goal_role="ai_ml_specialist", completed=done)["roles"][0]["edge_now"]
    assert after > before


def test_pathway_only_uses_catalog_items():
    ids = {i["id"] for i in DATA["catalog"]}
    pw = scoring.one_move_and_pathway(RAVI["skills"], "ai_ml_specialist", DATA, "fast")
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
    parsed = c.post("/api/profile/upload", files={"file": ("ravi.pdf", _pdf, "application/pdf")}).json()["skills"]
    assert "python" in parsed and parsed["python"]["evidence"]
    assert c.get("/api/sample-cvs/ravi.pdf").status_code == 200
    assert c.get("/api/sample-cvs/nobody.pdf").status_code == 404
    assert c.get("/api/does-not-exist").status_code == 404
    assert c.post("/api/profile/upload", files={"file": ("x.pdf", b"not a pdf", "application/pdf")}).status_code == 400
    f = c.post("/api/forecast", json={"skills": RAVI["skills"], "scenario": "fast"}).json()
    assert f["is_estimate"] and f["trend_source"]["source"]
    p = c.post("/api/pathway", json={"skills": RAVI["skills"], "role_id": "ai_ml_specialist"}).json()
    assert p["steps"]
    assert c.post("/api/forecast", json={"skills": {"nope": 1}}).status_code == 400


def test_parser_only_returns_catalog_skills_with_evidence():
    text = "I built a quantum teleporter in Python and led a team. I know basic SQL."
    found = parse_skills(text, DATA["skills"])
    assert set(found) <= set(DATA["skills"])
    assert found["python"]["level"] > found["sql"]["level"]
    assert all(f["evidence"] for f in found.values())


def test_roles_are_built_from_sources():
    for r in DATA["roles"].values():
        assert r["wage"]["median_myr"] > 0 and "DOSM" in r["wage"]["source"]
        o = r["outlook"]
        if o.get("net_growth_2030") is not None:
            assert "WEF" in o["source"] and "p." in o["source"]
    assert DATA["roles"]["data_entry_clerk"]["outlook"]["malaysia_net_growth_2030"] == -28
    assert DATA["roles"]["cybersecurity_specialist"]["mycol"]["masco"] == "2531"


def test_job_market_moves_the_score():
    """Same skills, growing vs shrinking market: the growing role should gain over time."""
    sk = {"data_entry": 0.9, "excel_reporting": 0.9, "ownership": 0.9}
    f = scoring.forecast(sk, DATA, "moderate")
    r = {x["role_id"]: x for x in f["roles"]}
    assert r["data_entry_clerk"]["timeline"][-1]["market"] < 1 < r["ai_ml_specialist"]["timeline"][-1]["market"]
    assert r["data_entry_clerk"]["at_risk"]


def test_soft_skills_alone_do_not_qualify_for_specialist_roles():
    sk = {"communication": 0.9, "ownership": 0.9, "critical_thinking": 0.9}
    r = {x["role_id"]: x for x in scoring.forecast(sk, DATA)["roles"]}
    assert r["medical_specialist"]["core_gate"] == 0.5


def test_human_skills_gain_ai_exposure_slower_than_technical_skills():
    """Tool-level AI reaches human skills at a quarter of the speed (scoring.HUMAN_TOOLS_FACTOR)."""
    trends = DATA["trends"]
    for sk in DATA["skills"].values():
        if sk["category"] != "human":
            continue
        rise = scoring.exposure(sk, 3, "fast", trends) - scoring.exposure(sk, 0, "fast", trends)
        as_technical = scoring.exposure({**sk, "category": "technical"}, 3, "fast", trends) - scoring.exposure(sk, 0, "fast", trends)
        assert rise <= as_technical * scoring.HUMAN_TOOLS_FACTOR + 1e-9


def test_shrinking_research_slows_tools_but_never_below_half_speed():
    assert scoring.tools(3, "fast", -0.2) < scoring.tools(3, "fast", 0.0)
    assert scoring.tools(3, "fast", -0.9) == scoring.tools(3, "fast", -0.5)


def test_sdg_focus_changes_ranking_but_never_the_edge_score():
    plain = {r["role_id"]: r for r in scoring.forecast(RAVI["skills"], DATA, "moderate")["roles"]}
    focus = scoring.forecast(RAVI["skills"], DATA, "moderate", sdg_focus=["climate"])["roles"]
    for r in focus:
        assert r["edge_y3"] == plain[r["role_id"]]["edge_y3"]          # score is honest, unchanged
        if "climate" in r["sdg_themes"]:
            assert (r["rank_score"] > r["edge_y3"] or r["edge_y3"] == 0) and "sdg" in r["explain"]
        else:
            assert r["rank_score"] == r["edge_y3"]
    assert any(r["sdg_focus_match"] for r in focus) and not any(r["sdg_focus_match"] for r in plain.values())


def test_every_role_has_an_sdg_impact_line_and_a_theme():
    for rid, role in DATA["roles"].items():
        assert DATA["sdg_impact"]["roles"].get(rid)
        assert scoring.role_themes(role, DATA)


def test_pathway_reports_sdg_contribution_with_sources():
    p = scoring.one_move_and_pathway(RAVI["skills"], "renewable_energy_engineer", DATA)
    s = p["sdg_summary"]
    assert "7.2" in [t["target"] for t in s["targets"]]
    assert all(t["sources"] for t in s["targets"]) and s["impact"]


def test_fairness_same_cv_as_12_different_people_gives_identical_skills():
    from src.backend import fairness
    from src.backend.cv_extract import extract_cv, redact_text
    for pid in ["aiman", "meiling", "ravi", "nurul", "daniel"]:
        text = extract_cv((DATA_DIR / "sample_cvs" / f"{pid}.pdf").read_bytes(), f"{pid}.pdf")["raw_text"]
        rep = fairness.check(text, DATA["skills"])
        assert rep["passed"] and rep["people_tested"] == 12, (pid, rep["differences"])
    # every protected attribute line is actually removed before matching
    red = redact_text(fairness._as(fairness.PEOPLE[1], "Summary\nPython developer."))
    for word in ["Tan Wei Ming", "Gender", "Age", "Race", "Religion", "Marital"]:
        assert word not in red


def test_upload_returns_fairness_report():
    c = TestClient(app)
    r = c.post("/api/profile/upload", files={"file": ("ravi.pdf", _pdf, "application/pdf")}).json()
    assert r["fairness"]["passed"] is True
