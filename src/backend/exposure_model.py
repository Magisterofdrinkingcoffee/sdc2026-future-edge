"""Model 1 – AI-Exposure Model: inference in plain Python (no scikit-learn needed at runtime).

The model is trained by tools/train_exposure.py on 19,265 human-rated O*NET tasks and exported
to models/exposure_model.json. This file reproduces scikit-learn's TF-IDF + logistic regression
exactly: same tokeniser, same word pairs, sublinear tf, l2 norm, softmax.

    predict("Entered shipment records into SAP")
    -> {"E0": 0.08, "E1": 0.05, "E2": 0.87, "label": "E2", "top_words": [...]}
"""
import json
import math
import re
from functools import lru_cache
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "models" / "exposure_model.json"
TOKEN = re.compile(r"(?u)\b\w\w+\b")


@lru_cache(maxsize=1)
def load():
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def _features(text):
    toks = TOKEN.findall(text.lower())
    grams = toks + [f"{a} {b}" for a, b in zip(toks, toks[1:])]
    counts = {}
    for g in grams:
        counts[g] = counts.get(g, 0) + 1
    return counts


def predict(text, explain=3):
    m = load()
    vocab, classes = m["vocab"], m["classes"]
    weights = {}
    for term, tf in _features(text).items():
        entry = vocab.get(term)
        if entry:
            weights[term] = (1 + math.log(tf)) * entry[0]
    norm = math.sqrt(sum(w * w for w in weights.values())) or 1.0
    scores = list(m["intercept"])
    contrib = {}
    for term, w in weights.items():
        x = w / norm
        coefs = vocab[term][1:]
        for k in range(len(classes)):
            scores[k] += x * coefs[k]
        contrib[term] = x * (coefs[2] + 0.5 * coefs[1] - coefs[0])  # pushes towards "AI can do it"
    top = max(scores)
    exps = [math.exp(s - top) for s in scores]
    total = sum(exps)
    probs = {c: e / total for c, e in zip(classes, exps)}
    ranked = sorted(contrib.items(), key=lambda kv: -abs(kv[1]))[:explain]
    return {**{c: round(p, 4) for c, p in probs.items()},
            "label": max(probs, key=probs.get),
            "known_words": len(weights),
            "top_words": [{"term": t, "towards": "AI" if v > 0 else "human"} for t, v in ranked]}


def metrics():
    return load()["metrics"]


def info():
    m = load()
    return {k: m[k] for k in ("name", "version", "classes", "class_meaning", "data", "metrics")}
