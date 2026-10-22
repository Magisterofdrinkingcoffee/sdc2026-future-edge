"""Tests for Model 2 (trend forecaster), Model 3 (Catch the AI) and the data-fusion range."""
import copy
import math

from fastapi.testclient import TestClient

from src.backend import catch_the_ai, scoring, trend_model, trends
from src.backend.data_store import load
from src.backend.main import app

DATA = load()


# ---------------- Model 2 ----------------
def test_trend_model_recovers_known_growth():
    counts = [round(100 * 1.02 ** t) for t in range(36)]  # +2%/month = +26.8%/year
    f = trend_model.fit(counts, phi=1.0)  # undamped: must recover the true growth
    assert abs(f["growth"] - (1.02 ** 12 - 1)) < 0.03
    assert abs(f["past_growth"] - (1.02 ** 12 - 1)) < 0.03
    assert f["growth_low"] <= f["growth"] <= f["growth_high"]
    assert len(f["forecast"]) == 36 and f["forecast"][0]["low"] <= f["forecast"][0]["mid"] <= f["forecast"][0]["high"]


def test_noisier_data_gives_a_wider_range():
    smooth = [round(100 * 1.02 ** t) for t in range(36)]
    noisy = [c + (25 if t % 2 else -25) for t, c in enumerate(smooth)]
    a, b = trend_model.fit(smooth), trend_model.fit(noisy)
    assert (b["growth_high"] - b["growth_low"]) > (a["growth_high"] - a["growth_low"])


def test_backtest_beats_naive_on_a_growing_series():
    bt = trend_model.backtest([round(50 * 1.04 ** t) for t in range(36)], phi=1.0)
    assert bt["model_error"] < bt["naive_error"]


def test_trends_build_structure():
    sig = [{"id": "x", "label": "X", "query": "q"}]
    monthly = {"x": {f"2024-{m:02d}": 10 + m for m in range(1, 13)} | {f"2025-{m:02d}": 25 + m for m in range(1, 13)}
                    | {f"2026-{m:02d}": 40 + m for m in range(1, 13)}}
    d = trends.build(monthly, sig, "2026-10-22T00:00:00+00:00")
    s = d["signals"]["x"]
    assert s["growth"] > 0 and s["growth_low"] < s["growth_high"] and s["forecast"][0]["month"] == "2027-01"
    assert d["backtest"]["signals"] == 1


# ---------------- Model 3 ----------------
def test_public_pack_does_not_leak_answers():
    p = catch_the_ai.public_pack("engineering")
    assert "error" not in str(p["lines"]) and "why" not in str(p)


def errors_of(pack):
    return [i for i, l in enumerate(catch_the_ai.content()["packs"][pack]["lines"]) if l["error"]]


def test_finding_mistakes_and_owning_them_scores_higher():
    errs = errors_of("business")
    best = catch_the_ai.score("business", errs, 90, "fix_tell", {"q2": 3, "q4": 2})
    blind = catch_the_ai.score("business", [], 100, "send", {"q2": 0, "q4": 0})
    assert best["judgment"] > 0.9 > blind["judgment"] and best["responsibility"] > blind["responsibility"]
    assert best["details"]["all_found"] and blind["details"]["overconfident"]


def test_false_alarms_lower_judgment():
    errs = errors_of("it")
    clean = [i for i in range(7) if i not in errs]
    exact = catch_the_ai.score("it", errs, 100, "fix_tell")
    flag_all = catch_the_ai.score("it", errs + clean, 100, "fix_tell")
    assert exact["judgment"] > flag_all["judgment"]


def test_every_pack_has_planted_mistakes_and_clean_lines():
    for pid, p in catch_the_ai.content()["packs"].items():
        n = sum(1 for l in p["lines"] if l["error"])
        assert 2 <= n < len(p["lines"]), pid


def test_catch_api():
    c = TestClient(app)
    p = c.get("/api/catch", params={"sector": "Digital & ICT"}).json()
    assert p["pack"] == "it"
    r = c.post("/api/catch", json={"pack": "it", "flagged": errors_of("it"), "confidence": 80, "action": "fix_tell",
                                   "answers": {"q2": 3, "q4": 2}}).json()
    assert r["judgment_range"][0] <= r["judgment"] <= r["judgment_range"][1]
    assert c.post("/api/catch", json={"pack": "nope"}).status_code == 404


# ---------------- Data fusion range ----------------
def test_edge_range_contains_the_central_estimate():
    a = catch_the_ai.score("engineering", errors_of("engineering")[:2], 70, "fix_tell", {"q2": 3, "q4": 2})
    f = scoring.forecast({"power_systems": 0.7, "python": 0.5}, DATA, "fast", assessment=a)
    for r in f["roles"]:
        for t in r["timeline"]:
            assert t["low"] <= t["edge"] <= t["high"]


def test_wider_trend_uncertainty_gives_a_wider_edge_range():
    d = copy.deepcopy(DATA)
    for s in d["trends"]["signals"].values():
        g = s.get("growth") or 0
        s["growth_low"], s["growth_high"] = g - 0.05, g + 0.05
    d2 = copy.deepcopy(d)
    for s in d2["trends"]["signals"].values():
        g = s.get("growth") or 0
        s["growth_low"], s["growth_high"] = g - 0.6, g + 0.6
    sk = {"python": 0.7, "sql": 0.7, "web_dev": 0.7}
    w1 = scoring.forecast(sk, d, "fast")["roles"]
    w2 = scoring.forecast(sk, d2, "fast")["roles"]
    r1 = {r["role_id"]: r["edge_y3_range"] for r in w1}["software_developer"]
    r2 = {r["role_id"]: r["edge_y3_range"] for r in w2}["software_developer"]
    assert (r2[1] - r2[0]) > (r1[1] - r1[0])


def test_damping_is_chosen_from_training_months_only():
    # steady exponential growth -> no damping needed
    steady = [[round(100 * 1.03 ** t) for t in range(36)] for _ in range(3)]
    assert trend_model.select_phi(steady)[0] == 1.0
    # boom then flat inside the training window -> damping wins
    boom = [[round(20 * 1.15 ** min(t, 8)) for t in range(36)] for _ in range(3)]
    assert trend_model.select_phi(boom)[0] < 1.0
    # changing the test year (months 24-35) must not change the choice
    changed = [s[:24] + [9999] * 12 for s in boom]
    assert trend_model.select_phi(changed)[0] == trend_model.select_phi(boom)[0]


def test_damped_growth_is_smaller_than_past_trend():
    f = trend_model.fit([round(100 * 1.05 ** t) for t in range(36)], phi=0.8)
    assert 0 < f["growth"] < f["past_growth"]
