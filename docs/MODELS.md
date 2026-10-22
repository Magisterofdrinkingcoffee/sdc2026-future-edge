# Future Edge – models and data fusion

Future Edge combines **three models** with real Malaysian job-market data. Each section below is a model card: what it does, the data, how it was checked, and its limits.

```
CV sentences ──► Model 1  AI-exposure (trained, 19,265 human-rated tasks) ─┐
arXiv papers ──► Model 2  trend forecaster (36 months, 80% range) ─────────┼─► DATA FUSION ─► Edge Score (low–mid–high)
Catch the AI ──► Model 3  judgment & responsibility (exact scoring) ───────┘        ▲
WEF / DOSM / MyCOL ──────────────────────────────────────────── job market ─────────┘
```

---

# Model 1 – AI-Exposure Model

**What it does:** reads a description of work (a skill, or a sentence from the user's CV) and estimates how much of it AI can do:

| Label | Meaning |
|---|---|
| E0 | AI can't meaningfully speed this up |
| E1 | an AI chatbot alone can cut the time by at least half |
| E2 | AI can do it once extra software tools are built on top |

**Training data:** 19,265 task statements from the US O*NET database, each labelled by **human annotators** in Eloundou et al. (2023), *"GPTs are GPTs: An Early Look at the Labor Market Impact Potential of Large Language Models"*. Data: github.com/openai/GPTs-are-GPTs (MIT licence), copied to `src/database/onet_task_exposure.tsv`. O*NET is CC BY 4.0.

**Model:** TF-IDF (single words + word pairs, sublinear tf, l2 norm) → multinomial logistic regression (C = 4). Trained with `python -m tools.train_exposure` (needs `tools/requirements-train.txt`). Exported to `src/backend/models/exposure_model.json` and run in plain Python by `src/backend/exposure_model.py`, so the app doesn't need scikit-learn. A test checks that the plain-Python model gives the same probabilities as scikit-learn.

**Evaluation:** 5-fold cross-validation where every test fold contains **only occupations the model never saw** (GroupKFold by occupation, 798 occupations).

| Metric | Value |
|---|---|
| Accuracy | **73.4%** (±1.3%) |
| Simple guess (always "E0") | 53.2% |
| Macro F1 | 0.657 |
| Recall E0 / E1 / E2 | 86.7% / 39.4% / 66.9% |

**How the app uses it**
- Every skill in `skills.json` has a `task` description, and the model reads it.
- If the user's CV has a sentence for that skill, the model also reads **that sentence** and blends it 50/50 with the general reading. This is skipped for human skills (the sentence describes the context, not the skill) and when the model recognises fewer than 3 words.
- `exposure(t) = E1 + E2 × tools(t)`, where `tools(t)` grows each year faster in the "fast" scenario and in areas where arXiv research is growing faster (the trend layer).

**Limitations, stated honestly**
- The labels describe **US** jobs as of 2023, while the app applies them to Malaysia. Job-market data comes from Malaysian sources (WEF Malaysia profile, DOSM, MyCOL).
- The model only understands words it saw in O*NET tasks. Product names (e.g. "PostgreSQL") are often unknown.
- It's weakest at E1 ("chatbot alone") tasks and sometimes reacts to single words (e.g. "explain").
- Exposure means **AI can do part of the work**, not "the job disappears". All results are labelled estimates and are never used for hiring decisions.

---

# Model 2 – AI-Trend Forecaster

**What it does:** estimates how fast AI capability is growing in each area (code generation, document AI, smart grids…), with an **80% range**, and projects the next 3 years.

**Data:** new arXiv papers per month for each of the 10 signals in `src/backend/data/signals.json`, for the 36 full months Oct 2023 – Sep 2026, collected from the arXiv API (360 requests, 3+ s apart). Collect (resumable, ~20 min, standard library only): `python -m tools.collect_arxiv`; it saves to `src/database/arxiv_monthly.json` after every answer and then rebuilds `data/trends.json`. Rebuild only: `python -m tools.build_trends`. Live refresh on Replit: the "Refresh trend data" button (or `python -m src.backend.trends`).

**Model:** a damped log-linear trend per signal. (1) Ordinary least squares on `log(papers + 1) = a + b × month`. (2) Project forward from the last fitted month with the slope fading by φ each month: level after h months = level + b × (φ + φ² + … + φʰ) (Gardner & McKenzie, 1985). Growth used by the app = expected change over the next 12 months = `exp(b × (φ + … + φ¹²)) − 1`; its 80% interval comes from the standard error of `b`; forecasts carry an 80% prediction band. The undamped past trend `exp(12b) − 1` is shown next to it. Code: `src/backend/trend_model.py` (plain Python).

**Choosing φ without peeking:** `select_phi()` uses only the first 24 months of every signal (fit on months 1–12, predict 13–24) over φ ∈ {1.0, 0.95, …, 0.5} and takes the largest φ within 0.005 of the best mean error. On the real data it picks **φ = 0.8**. A test checks that changing the test year does not change the choice.

**Validation (backtest, real arXiv data, collected 22 Oct 2026):** fit on the first 24 months, predict the total papers in the last 12 months, compare with the naive guess "next year = last year".

| | mean error | better than naive | real total inside 80% band |
|---|---|---|---|
| Plain log-linear trend (first version) | 29.5% | 5 of 10 | 9 of 10 |
| **Damped trend (φ = 0.8, used)** | **17.2%** | **6 of 10** | **10 of 10** |
| Naive "same as last year" | 22.7% | – | – |

We kept the first version's result here on purpose: a plain exponential over-shot because AI research boomed in 2023–24 and is now slowing (e.g. LLM code generation grew +48%/yr over the period but only +13% is expected next year).

**Real results (expected growth next 12 months, 80% range):** LLM agents +27% (25–30), human-AI collaboration +18% (15–21), LLM code generation +13% (11–15), document AI +13% (10–15), LLMs for data analysis +5% (3–7), visual inspection +5% (3–8), conversational AI +4% (2–6), AI security +2% (−1–6), smart grids −2% (−5–0), AutoML −3% (−5–0).

**Limitations:** research papers are a *proxy* for AI capability, not a direct measure; trends can't predict sudden breakthroughs; several queries have only 2–20 papers a month (AutoML, smart grids, AI security), so their trends are noisy (R² < 0.1) and the model is only slightly better than the naive guess there. The 80% range reflects uncertainty in the slope, not in which queries we chose.

---

# Model 3 – "Catch the AI" (judgment & responsibility)

**What it does:** instead of asking people to rate themselves, it **tests** them. The user reviews a short AI-written piece of work from their field (business report, electrical site note, or login code) with **planted mistakes** (wrong maths, numbers that don't add up, an invented source, a safety error), flags the lines they would not send, says how sure they are, chooses what to do next, and answers two responsibility situations.

**Scoring (exact, no AI needed – we know where the mistakes are):**
```
judgment       = 0.60 × share of planted mistakes found
               + 0.25 × (1 − share of correct lines flagged)      # no panic-flagging
               + 0.15 × calibration (1 − |confidence − share found|)
responsibility = 0.50 × action chosen (send as is … fix + tell manager + disclose AI)
               + 0.50 × two responsibility situations
range          = ± 0.10 judgment, ± 0.08 responsibility (one short exercise is a small sample)
```
Content: `src/backend/data/catch_the_ai.json`. Code: `src/backend/catch_the_ai.py`.

**Why this design:** there is no labelled data for "judgment", so training a model would only learn our own opinions. A performance test with known answers is objective and explainable. It measures the exact skill the app is about: judging AI output. WEF Future of Jobs 2025 (Malaysia profile, p. 168) reports that 71% of employers in Malaysia see analytical thinking as a core skill.

**Limitations:** one short exercise, not a personality measurement; the packs are few and could be memorised; results are shown as estimates and never used for hiring decisions.

---

# Data fusion – the Edge Score

```
Edge(t) = 100 × [AI-adjusted fit(t) / best possible fit]        # Model 1 + Model 2
              × [0.60 + 0.25 × human skills + 0.15 × rarity]      # Model 3 + rare skill mix
              × job market(t)                                     # WEF net job growth (Malaysia first)
              × core-skill check                                  # 0.5 + 0.5 × level in the role's core skills
```
* **AI-adjusted fit** counts each of the role's skills only for the part AI can't do in year t:
  `exposure(t) = E1 + E2 × tools(t)` (Model 1), where `tools(t)` grows faster with Model 2's research growth and in the "fast" scenario.
* **Range:** low = Model 2's upper growth (AI arrives faster) + Model 3's lower bound; high = the opposite. Shown on every forecast day.
* Weights are **designed, not learned** (there is no outcome data to learn them from); they are documented here and in `src/backend/scoring.py`, and every number in the app has a plain-English "why".
