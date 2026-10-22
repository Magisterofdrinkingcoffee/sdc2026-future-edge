"""Model 3 – Edge Check: "Catch the AI".

Instead of asking people to rate their own judgment (everyone says 5/5), we TEST it:
the user reviews a short piece of AI-written work from their field with planted mistakes,
flags the lines they think are wrong, says how sure they are, and chooses what to do next.

Because we planted the mistakes, scoring is exact, explainable and needs no AI or training data:

  judgment       = 0.60 * share of planted mistakes found          (catches AI errors)
                 + 0.25 * (1 - share of correct lines flagged)     (doesn't panic at everything)
                 + 0.15 * calibration                              (knows what it doesn't know:
                                                                    1 - |confidence - share found|)
  responsibility = 0.50 * the action chosen afterwards (0-3)       (owns the outcome)
                 + 0.50 * the two responsibility situations (q2, q4 in assessment.json)

Result is an ESTIMATE from a ~2 minute exercise with a +/- range, never a verdict or a hiring decision.
"""
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / "data"
W_FOUND, W_PRECISION, W_CALIBRATION = 0.60, 0.25, 0.15
W_ACTION, W_SITUATIONS = 0.5, 0.5
# A 7-line exercise with 3 planted mistakes is a small sample: one mistake more or less moves
# "share found" by 0.33, i.e. judgment by ~0.2. We show half of that as the +/- range.
JUDGMENT_RANGE = 0.10
RESPONSIBILITY_RANGE = 0.08


@lru_cache(maxsize=1)
def content():
    return json.loads((DATA / "catch_the_ai.json").read_text(encoding="utf-8"))


def _assessment():
    return json.loads((DATA / "assessment.json").read_text(encoding="utf-8"))


def pack_for_sector(sector):
    c = content()
    return c["sector_to_pack"].get(sector or "", "business")


def public_pack(pack_id):
    """What the browser gets: the lines WITHOUT the answers."""
    c = content()
    if pack_id not in c["packs"]:
        raise KeyError(pack_id)
    p = c["packs"][pack_id]
    qs = {q["id"]: q for q in _assessment()["questions"]}
    return {
        "pack": pack_id, "title": p["title"], "context": p["context"],
        "lines": [l["text"] for l in p["lines"]],
        "n_mistakes_hint": "Some lines are wrong. Flag every line you would not send as it is.",
        "actions": {"question": c["actions"]["question"],
                    "options": [{"id": o["id"], "text": o["text"]} for o in c["actions"]["options"]]},
        "situations": [{"id": qid, "text": qs[qid]["text"], "options": [o["text"] for o in qs[qid]["options"]]}
                       for qid in c["responsibility_questions"]],
    }


def clamp01(x):
    return max(0.0, min(1.0, x))


def score(pack_id, flagged, confidence, action_id, answers=None):
    """flagged: line indexes the user marked as wrong; confidence: 0-100; answers: {q2: idx, q4: idx}."""
    c = content()
    p = c["packs"][pack_id]
    lines = p["lines"]
    flagged = {int(i) for i in flagged if 0 <= int(i) < len(lines)}
    errors = {i for i, l in enumerate(lines) if l["error"]}
    clean = set(range(len(lines))) - errors

    hits, misses, false_alarms = flagged & errors, errors - flagged, flagged & clean
    found = len(hits) / len(errors)
    precision_part = 1 - len(false_alarms) / len(clean)
    conf = clamp01((confidence or 0) / 100)
    calibration = 1 - abs(conf - found)
    judgment = W_FOUND * found + W_PRECISION * precision_part + W_CALIBRATION * calibration

    action = next((o for o in c["actions"]["options"] if o["id"] == action_id), None)
    action_part = action["responsibility"] / 3 if action else 0.0
    qs = {q["id"]: q for q in _assessment()["questions"]}
    sit = []
    for qid in c["responsibility_questions"]:
        idx = (answers or {}).get(qid)
        if idx is not None and 0 <= idx < len(qs[qid]["options"]):
            sit.append(qs[qid]["options"][idx]["responsibility"] / 3)
    responsibility = W_ACTION * action_part + W_SITUATIONS * (sum(sit) / len(sit)) if sit else action_part

    overconfident = conf - found >= 0.34
    return {
        "judgment": round(judgment, 3),
        "responsibility": round(responsibility, 3),
        "judgment_range": [round(clamp01(judgment - JUDGMENT_RANGE), 3), round(clamp01(judgment + JUDGMENT_RANGE), 3)],
        "responsibility_range": [round(clamp01(responsibility - RESPONSIBILITY_RANGE), 3),
                                 round(clamp01(responsibility + RESPONSIBILITY_RANGE), 3)],
        "answered": len(sit) + 1,
        "method": "catch_the_ai",
        "pack": pack_id,
        "details": {
            "found": len(hits), "planted": len(errors), "false_alarms": len(false_alarms),
            "confidence": round(conf, 2), "calibration": round(calibration, 2), "overconfident": overconfident,
            "action": action_id, "all_found": not misses and not false_alarms,
        },
        "feedback": {
            "mistakes": [{"line": i, "text": lines[i]["text"], "type": lines[i]["error"]["type"],
                          "why": lines[i]["error"]["why"], "found": i in hits} for i in sorted(errors)],
            "false_alarms": [{"line": i, "text": lines[i]["text"]} for i in sorted(false_alarms)],
        },
        "explain": [
            f"You caught {len(hits)} of {len(errors)} planted mistakes"
            + (f" and flagged {len(false_alarms)} correct line(s)." if false_alarms else " with no false alarms."),
            f"You were {round(conf * 100)}% sure; you actually found {round(found * 100)}%"
            + (" (overconfident)." if overconfident else "."),
            f"Afterwards you chose: \"{action['text']}\"" if action else "You didn't choose what to do next.",
        ],
        "is_estimate": True,
        "note": "Estimate from a 2-minute exercise. Not a verdict and never a hiring decision.",
    }
