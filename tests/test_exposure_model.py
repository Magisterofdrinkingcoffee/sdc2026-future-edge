"""Tests for Model 1 (AI-exposure model). Run: python -m pytest -q"""
import json

import pytest

from src.backend import scoring
from src.backend.data_store import DATA_DIR, load
from src.backend.exposure_model import MODEL_PATH, metrics, predict

DATA = load()


def exposure_now(text):
    p = predict(text)
    return p["E1"] + p["E2"] * scoring.TOOLS_NOW


def test_model_beats_simple_guess_on_unseen_occupations():
    m = metrics()
    assert "unseen" in m["evaluation"]
    assert m["accuracy"] > m["baseline_accuracy"] + 0.1


def test_probabilities_are_valid():
    p = predict("Prepare weekly sales reports in Excel")
    assert abs(p["E0"] + p["E1"] + p["E2"] - 1) < 1e-3 and p["label"] in ("E0", "E1", "E2")


def test_model_ranks_obvious_cases_sensibly():
    assert exposure_now("Write Python scripts to automate data processing") > exposure_now("Repair hydraulic machinery on the factory floor")
    assert exposure_now("Enter data from invoices into the accounting system") > exposure_now("Inspect electrical wiring at construction sites")


def test_every_skill_has_a_model_reading():
    for s in DATA["skills"].values():
        assert s["task"] and abs(s["model"]["E0"] + s["model"]["E1"] + s["model"]["E2"] - 1) < 1e-3


def test_your_own_cv_sentence_changes_the_forecast():
    sk = {"python": 0.7, "sql": 0.5}
    plain = scoring.forecast(sk, DATA, "moderate")
    mine = scoring.forecast(sk, DATA, "moderate", evidence={"python": "Repaired and calibrated laboratory instruments using Python"})
    p = {r["skill"]: r for r in plain["skills"]}["python"]
    m = {r["skill"]: r for r in mine["skills"]}["python"]
    assert m["model"]["personal"] and m["exposure_now"] != p["exposure_now"]


def test_human_skills_ignore_context_sentences():
    out = scoring.forecast({"ownership": 0.7}, DATA, evidence={"ownership": "Responsible for data entry of all shipment records"})
    assert not out["skills"][0]["model"]["personal"]


def test_fast_scenario_brings_ai_tools_sooner():
    s = DATA["skills"]["data_entry"]
    assert scoring.exposure(s, 3, "fast", DATA["trends"]) >= scoring.exposure(s, 3, "moderate", DATA["trends"])
    assert scoring.exposure(s, 0, "fast", DATA["trends"]) == scoring.exposure(s, 0, "moderate", DATA["trends"])


def test_plain_python_model_matches_scikit_learn():
    """The app runs the exported model without scikit-learn; it must give the same answers."""
    pd = pytest.importorskip("pandas")
    pytest.importorskip("sklearn")
    from tools.train_exposure import DATA as TASKS, make_model
    d = pd.read_csv(TASKS, sep="\t")
    m = make_model().fit(d.task.values, d.human_label.values)
    sample = d.sample(200, random_state=0).task.tolist()
    sk = m.predict_proba(sample)
    for row, text in zip(sk, sample):
        p = predict(text)
        assert max(abs(row[i] - p[c]) for i, c in enumerate(["E0", "E1", "E2"])) < 1e-3


def test_model_file_records_its_data_source_and_licence():
    meta = json.loads(MODEL_PATH.read_text())
    assert "MIT" in meta["data"] and "O*NET" in meta["data"]


def test_bare_skill_lists_fall_back_to_the_general_reading():
    out = scoring.forecast({"python": 0.7}, DATA, evidence={"python": "Python, JavaScript, SQL, Git and GitHub, HTML/CSS."})
    assert not out["skills"][0]["model"]["personal"]
