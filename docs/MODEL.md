# Model 1 – AI-Exposure Model (model card)

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
