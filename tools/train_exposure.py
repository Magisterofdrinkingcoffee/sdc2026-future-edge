"""Model 1 – AI-Exposure Model. Training script.

    pip install scikit-learn pandas      (training only – the app itself does not need them)
    python -m tools.train_exposure

Data: src/database/onet_task_exposure.tsv – 19,265 real job tasks from the US O*NET database,
each rated by HUMAN annotators for exposure to large language models (Eloundou et al., 2023,
"GPTs are GPTs", github.com/openai/GPTs-are-GPTs, MIT licence):
    E0 = no exposure: an LLM can't reduce the time for this task
    E1 = direct exposure: an LLM alone can cut the time by at least half
    E2 = exposure with extra software built on top of LLMs

Model: TF-IDF (words + word pairs) -> multinomial logistic regression.
Evaluation: 5-fold cross-validation where each test fold contains ONLY occupations the model
never saw in training (GroupKFold by occupation), so the score reflects new jobs, not memory.

Output: src/backend/models/exposure_model.json – vocabulary, idf weights and coefficients,
so the app can run the model in plain Python (src/backend/exposure_model.py) without scikit-learn.
"""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "database" / "onet_task_exposure.tsv"
OUT = ROOT / "src" / "backend" / "models" / "exposure_model.json"

# Hyper-parameters (chosen by grouped cross-validation; see README "Model 1")
NGRAM = (1, 2)
MIN_DF = 2
C = 4.0
CLASSES = ["E0", "E1", "E2"]


def make_model():
    return make_pipeline(
        TfidfVectorizer(ngram_range=NGRAM, min_df=MIN_DF, sublinear_tf=True, lowercase=True),
        LogisticRegression(max_iter=3000, C=C),
    )


def main():
    d = pd.read_csv(DATA, sep="\t")
    X, y = d.task.values, d.human_label.values
    groups = d.soc_code.str[:7].values  # occupation, ignoring O*NET sub-specialisations

    # ---- evaluation on unseen occupations -------------------------------------------------
    preds, accs, f1s, base = np.empty(len(d), dtype=object), [], [], []
    for tr, te in GroupKFold(5).split(X, y, groups):
        m = make_model().fit(X[tr], y[tr])
        p = m.predict(X[te])
        preds[te] = p
        accs.append(accuracy_score(y[te], p))
        f1s.append(f1_score(y[te], p, average="macro"))
        base.append((y[te] == pd.Series(y[tr]).mode()[0]).mean())
    cm = confusion_matrix(y, preds, labels=CLASSES)
    per_class = {c: round(float(cm[i, i] / cm[i].sum()), 3) for i, c in enumerate(CLASSES)}
    metrics = {
        "evaluation": "5-fold cross-validation, test folds contain only occupations unseen in training",
        "accuracy": round(float(np.mean(accs)), 3), "accuracy_std": round(float(np.std(accs)), 3),
        "macro_f1": round(float(np.mean(f1s)), 3),
        "baseline_accuracy": round(float(np.mean(base)), 3),
        "baseline": "always predict the most common label (E0)",
        "recall_per_class": per_class,
        "confusion_matrix": {"labels": CLASSES, "rows_true_cols_pred": cm.tolist()},
        "n_tasks": int(len(d)), "n_occupations": int(pd.Series(groups).nunique()),
    }
    print(json.dumps(metrics, indent=2))

    # ---- final model on all data, exported for plain-Python inference --------------------
    m = make_model().fit(X, y)
    vec, clf = m.named_steps["tfidfvectorizer"], m.named_steps["logisticregression"]
    assert list(clf.classes_) == CLASSES
    terms = vec.get_feature_names_out()
    coef = clf.coef_.T  # (n_terms, 3)
    model = {
        "name": "Future Edge AI-Exposure Model",
        "version": date.today().isoformat(),
        "classes": CLASSES,
        "class_meaning": {"E0": "AI can't speed this up", "E1": "an AI chatbot alone can halve the time",
                          "E2": "AI can do it with extra tools built on top"},
        "data": "Eloundou et al. (2023) 'GPTs are GPTs' human exposure labels on O*NET task statements "
                "(github.com/openai/GPTs-are-GPTs, MIT licence); O*NET (CC BY 4.0)",
        "features": {"type": "tfidf", "ngram_range": list(NGRAM), "lowercase": True, "sublinear_tf": True,
                     "norm": "l2", "token_pattern": r"(?u)\b\w\w+\b"},
        "intercept": [round(float(v), 6) for v in clf.intercept_],
        "vocab": {t: [round(float(vec.idf_[i]), 5), *[round(float(c), 5) for c in coef[i]]]
                  for i, t in enumerate(terms) if np.abs(coef[i]).max() > 1e-4},
        "metrics": metrics,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(model, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size / 1e6:.1f} MB, {len(model['vocab'])} terms)")


if __name__ == "__main__":
    main()
